import logging
from typing import Dict, Any
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from apps.credentials.models import UserCredential, Tool, decrypt_secret
from apps.credentials.services import refresh_google_token # Import our new service
from django.conf import settings

import base64
import json
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

def _get_gmail_service(user):
    """Helper to get an authenticated Gmail service."""
    try:
        credential = UserCredential.objects.get(
            user=user,
            credential_type=Tool.ToolType.GMAIL
        )
        
        if credential.is_expired():
            creds = refresh_google_token(credential)
        else:
            creds = Credentials(
                token=decrypt_secret(credential.encrypted_access_token),
                refresh_token=decrypt_secret(credential.encrypted_refresh_token),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
            )
        
        return build('gmail', 'v1', credentials=creds)
    except UserCredential.DoesNotExist:
        return None

def _read_gmail_inbox(service) -> str:
    """Reads the user's Gmail inbox."""
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])
    
    email_summaries = []
    if not messages:
        email_summaries.append("No new messages found.")
    else:
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            snippet = msg.get('snippet', 'No snippet.')
            email_summaries.append(f"From: {sender}\nSubject: {subject}\nSnippet: {snippet}\n---")
    
    return "\n".join(email_summaries)

def _send_gmail(service, to: str, subject: str, body: str) -> str:
    """Sends an email."""
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        return f"Email sent successfully to {to}."
    except Exception as e:
        return f"Failed to send email: {str(e)}"

def _search_gmail(service, query: str) -> str:
    """Searches for emails."""
    results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
    messages = results.get('messages', [])
    
    if not messages:
        return f"No emails found matching query: '{query}'"
    
    summaries = []
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
        headers = msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        snippet = msg.get('snippet', 'No snippet.')
        summaries.append(f"ID: {message['id']}\nFrom: {sender}\nSubject: {subject}\nSnippet: {snippet}\n---")
        
    return "\n".join(summaries)

def _get_thread(service, thread_id: str) -> str:
    """Retrieves a specific email thread."""
    try:
        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        messages = thread.get('messages', [])
        
        thread_content = []
        for msg in messages:
            headers = msg.get('payload', {}).get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            snippet = msg.get('snippet', 'No snippet.')
            thread_content.append(f"From: {sender}\nSnippet: {snippet}\n")
            
        return "\n---\n".join(thread_content)
    except Exception as e:
        return f"Failed to retrieve thread {thread_id}: {str(e)}"

def gmail_tool(state: dict, config: dict) -> dict:
    """
    Dispatcher tool for Gmail actions.
    Expected input (state.current_task) format:
    JSON string: {"action": "send_email", "to": "...", "subject": "...", "body": "..."}
    OR {"action": "search_emails", "query": "..."}
    OR {"action": "get_thread", "thread_id": "..."}
    OR {"action": "read_inbox"}
    """
    logger.info(f"--- Running Tool: gmail_tool ---")
    
    # Handle state being a dict or object
    if isinstance(state, dict):
        user = state.get('user')
    else:
        user = getattr(state, 'user', None)

    if not user:
        return {"current_task": "Error: User not authenticated for tool."}

    service = _get_gmail_service(user)
    if not service:
        return {"current_task": "Error: Gmail not connected. Please add it on the Connections page."}

    if isinstance(state, dict):
        input_str = state.get('current_task', '')
    else:
        input_str = getattr(state, 'current_task', '')
    
    # Default to read inbox if empty or not JSON
    action = 'read_inbox'
    params = {}

    try:
        if input_str.strip().startswith('{'):
            data = json.loads(input_str)
            action = data.get('action', 'read_inbox')
            params = data
        else:
            # Fallback for plain text input - treat as read inbox or maybe search?
            # For safety/backward compatibility, let's stick to read_inbox if it's generic,
            # but if it looks like a query we could search. 
            # For now, let's just log it and default to read_inbox to be safe.
            logger.info(f"Gmail tool received non-JSON input: {input_str}. Defaulting to read_inbox.")
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse Gmail tool input as JSON: {input_str}")
    
    output = ""
    try:
        if action == 'send_email':
            output = _send_gmail(service, params.get('to'), params.get('subject'), params.get('body'))
        elif action == 'search_emails':
            output = _search_gmail(service, params.get('query', ''))
        elif action == 'get_thread':
            output = _get_thread(service, params.get('thread_id'))
        elif action == 'read_inbox':
            output = _read_gmail_inbox(service)
        else:
            output = f"Error: Unknown Gmail action '{action}'"
            
    except Exception as e:
        logger.error(f"Gmail tool error: {e}")
        output = f"Error executing Gmail action: {e}"

    return {"current_task": output}