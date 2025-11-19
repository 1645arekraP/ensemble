from django.conf import settings
from django.db import models


class Tool(models.Model):
    """
    Defines a tool that an agent can use. Tools are converted to LangGraph-compatible
    tool definitions at runtime.
    """

    class ToolType(models.TextChoices):
        WEB_SEARCH = 'web_search', 'Web Search'
        DISCORD_WEBHOOK = 'discord_webhook', 'Discord Webhook'
        SLACK_WEBHOOK = 'slack_webhook', 'Slack Webhook'
        TEAMS_WEBHOOK = 'teams_webhook', 'Microsoft Teams Webhook'
        GMAIL = 'gmail', 'Google Mail'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="tools",
        null=True,
        blank=True
    )
    
    # Core fields
    name = models.CharField(
        max_length=100,
        help_text="Unique identifier for the tool (e.g., 'tavily_search', 'brave_search')"
    )
    description = models.TextField(
        help_text="Description for the LLM to understand when and how to use this tool."
    )
    tool_type = models.CharField(
        max_length=50,
        choices=ToolType.choices,
        default=ToolType.WEB_SEARCH
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tool-specific configuration. For web_search: {'api_key': '...', 'max_results': 5}"
    )

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.name} ({self.get_tool_type_display()})"
    

class mcp(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    url = models.URLField(max_length=200)

    def __str__(self):
        return self.name