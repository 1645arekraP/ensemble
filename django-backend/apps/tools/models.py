from django.db import models


class Tool(models.Model):
    """
    Defines a tool that an agent can use. Tools are converted to LangGraph-compatible
    tool definitions at runtime.
    """

    class ToolType(models.TextChoices):
        WEB_SEARCH = 'web_search', 'Web Search'
        # Add more later: CALCULATOR, DATABASE, API_CALL, etc.

    # Core fields
    name = models.CharField(
        max_length=100,
        unique=True,
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

    # Configuration for the tool (API keys, settings, etc.)
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

    def __str__(self):
        return f"{self.name} ({self.get_tool_type_display()})"