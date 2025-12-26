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
        POSTGRES = 'postgres', 'PostgreSQL Database'

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

    @property
    def effective_description(self):
        if self.tool_type == self.ToolType.GMAIL:
            return """A Gmail tool that can read your inbox, send emails, search for messages, and retrieve threads.
To use this tool, output a JSON string with an 'action' field.
Supported actions:
- Send email: {"action": "send_email", "to": "email@example.com", "subject": "...", "body": "..."}
- Search emails: {"action": "search_emails", "query": "from:sender@example.com"}
- Get thread: {"action": "get_thread", "thread_id": "..."}
- Read inbox: {"action": "read_inbox"}"""
        elif self.tool_type == self.ToolType.POSTGRES:
            return """A PostgreSQL database tool that can query databases, list tables, and describe table structures.
To use this tool, output a JSON string with an 'action' field.
Supported actions:
- Execute query: {"action": "execute_query", "query": "SELECT * FROM users LIMIT 10"}
- List tables: {"action": "list_tables"}
- Describe table: {"action": "describe_table", "table_name": "users"}
- Test connection: {"action": "test_connection"}
IMPORTANT: Be careful with UPDATE, DELETE, and INSERT queries as they will modify the database."""
        elif self.tool_type in [self.ToolType.DISCORD_WEBHOOK, self.ToolType.SLACK_WEBHOOK, self.ToolType.TEAMS_WEBHOOK]:
            return f"""A tool to send messages to {self.get_tool_type_display()}.
To use this tool, output a JSON string with an 'action' and 'message' field.
Example: {{"action": "send_message", "message": "Hello world"}}"""
        return self.description

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