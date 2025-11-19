# apps/tools/services/registry.py

from .functions import tavily_web_search
from . import webhooks, gmail

# This registry maps the 'tool_type' (from the Tool model's TextChoices) to the actual Python function that implements it.

TOOL_REGISTRY = {
    # Search Tools
    "web_search": tavily_web_search,

    # Notification Tools
    "discord_webhook": webhooks.send_discord_message,
    "slack_webhook": webhooks.send_slack_message,
    "teams_webhook": webhooks.send_teams_message,

    "gmail": gmail.read_gmail_inbox,
}