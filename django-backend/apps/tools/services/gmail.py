import logging
from typing import Dict, Any
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from apps.credentials.models import UserCredential, Tool, decrypt_secret
from apps.credentials.services import refresh_google_token # Import our new service
from django.conf import settings

logger = logging.getLogger(__name__)

def read_gmail_inbox(state: dict, config: dict) -> dict:
    """
    A tool function that reads the user's Gmail inbox.
    """
    logger.info(f"--- Running Tool: read_gmail_inbox ---")
    
    # Access user from state object (Pydantic model)
    user = getattr(state, 'user', None)
    if not user:
        logger.error("read_gmail_inbox: No user found in state.")
        return {"current_task": "Error: User not authenticated for tool."}

    try:
        # 1. Fetch the user's Gmail credential
        credential = UserCredential.objects.get(
            user=user,
            credential_type=Tool.ToolType.GMAIL
        )
        
        # 2. Check if expired and refresh if needed
        if credential.is_expired():
            creds = refresh_google_token(credential)
        else:
            # Just decrypt the valid token
            creds = Credentials(
                token=decrypt_secret(credential.encrypted_access_token),
                refresh_token=decrypt_secret(credential.encrypted_refresh_token),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
            )
        
        # 3. Build the Gmail API service
        service = build('gmail', 'v1', credentials=creds)
        
        # 4. Call the API
        results = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])
        
        email_summaries = []
        if not messages:
            email_summaries.append("No new messages found.")
        else:
            for message in messages:
                # Get metadata (headers and snippet)
                msg = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                snippet = msg.get('snippet', 'No snippet.')
                email_summaries.append(f"From: {sender}\nSubject: {subject}\nSnippet: {snippet}\n---")
        
        output = "\n".join(email_summaries)
        print(output)

    except UserCredential.DoesNotExist:
        logger.warning(f"read_gmail_inbox: No Gmail credential found for user {user.id}")
        output = "Error: Gmail not connected. Please add it on the Connections page."
    except Exception as e:
        logger.error(f"Gmail read failed: {e}")
        output = f"Error reading Gmail: {e}"

    # 5. Return the state update
    return {"current_task": output}