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

    # 2. Get the message from the state (assumed from previous agent)
    message = state.get('current_task', 'No content provided.')
    
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
        logger.info(f"Sending message to {service_name}: {message[:50]}...")
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status() # Raise an error for bad responses (4xx, 5xx)
        
        output_message = f"Successfully sent message to {service_name}."
        logger.info(output_message)
        state['current_task'] = output_message
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send {service_name} message: {e}")
        state['current_task'] = f"Error sending {service_name} message: {e}"
        
    return state

# --- Public functions that will be registered ---

def send_discord_message(state: dict, config: dict) -> dict:
    return _send_webhook_message(state, config, "Discord Webhook")

def send_slack_message(state: dict, config: dict) -> dict:
    return _send_webhook_message(state, config, "Slack Webhook")

def send_teams_message(state: dict, config: dict) -> dict:
    return _send_webhook_message(state, config, "Microsoft Teams Webhook")