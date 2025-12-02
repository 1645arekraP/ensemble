# apps/tools/services/webhooks.py

import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def _send_webhook_message(state: dict, config: dict, service_name: str) -> dict:
    """
    Generic helper to send a message to a webhook.
    It expects the webhook URL in config and the message in state['current_task'].
    """
    logger.info(f"--- Running Tool: {service_name} ---")
    
    # 1. Get the webhook URL from the Tool's config
    webhook_url = config.get('webhook_url')
    if not webhook_url:
        logger.error(f"{service_name}: No 'webhook_url' found in tool config.")
        state['current_task'] = f"Error: {service_name} tool is missing its webhook URL."
        return state

    # 2. Get the message from the state
    # The supervisor might send a JSON string like {"action": "send_message", "message": "..."}
    # or just a plain string.
    
    if isinstance(state, dict):
        input_task = state.get('current_task', '')
    else:
        input_task = getattr(state, 'current_task', '')

    message = input_task
    
    if isinstance(input_task, str) and input_task.strip().startswith('{'):
        try:
            import json
            data = json.loads(input_task)
            if 'message' in data:
                message = data['message']
        except json.JSONDecodeError:
            pass # Treat as plain text if not valid JSON
    
    # 3. Format the payload differently for each service
    if service_name == 'Discord Webhook':
        payload = {"content": message}
    elif service_name == 'Slack Webhook':
        payload = {"text": message}
    elif service_name == 'Microsoft Teams Webhook':
        payload = {"text": message}
    else:
        logger.error(f"Unknown webhook service: {service_name}")
        return state

    # 4. Send the request
    try:
        logger.info(f"Sending message to {service_name} at {webhook_url}")
        logger.info(f"Payload: {payload}")
        response = requests.post(webhook_url, json=payload)
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        response.raise_for_status() # Raise an error for bad responses (4xx, 5xx)
        
        output_message = f"Successfully sent message to {service_name}. Content: '{message}'"
        logger.info(output_message)
        
        if isinstance(state, dict):
            state['current_task'] = output_message
        else:
            # If it's a Pydantic model, we might need to return a dict update or rely on the runner to handle the return value.
            # The runner expects the tool to return a dict with keys to update in the state.
            # But the current implementation returns 'state'.
            # Let's return a dict update instead, which is the standard LangGraph/LangChain pattern often used.
            # However, looking at the function signature `-> dict`, it seems it expects to return the modified state or a dict update.
            # Let's check how `gmail_tool` does it. `gmail_tool` returns `{"current_task": output}`.
            # So we should probably change this function to return a dict update, not the state object itself.
            pass

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send {service_name} message: {e}")
        output_message = f"Error sending {service_name} message: {e}"
        
    return {"current_task": output_message}

# --- Public functions that will be registered ---

def send_discord_message(state: dict, config: dict) -> dict:
    return _send_webhook_message(state, config, "Discord Webhook")

def send_slack_message(state: dict, config: dict) -> dict:
    return _send_webhook_message(state, config, "Slack Webhook")

def send_teams_message(state: dict, config: dict) -> dict:
    return _send_webhook_message(state, config, "Microsoft Teams Webhook")