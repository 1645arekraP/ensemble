from django.db import models

class Tool(models.Model):
    """
    Defines a tool that an agent can use. The actual Python function is implemented
    separately in your agent logic.
    """
    TOOL_CHOICES = [
        #('api', 'API Call'),
        #('database', 'Database Query'),
        ('web_search', 'Web Search'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="The function name for the tool.")
    description = models.TextField(help_text="Description for the LLM to understand the tool's purpose.")
    tool_type = models.CharField(max_length=50, choices=TOOL_CHOICES, default='custom')

    configuration = models.JSONField(default=dict, blank=True, help_text="JSON configuration for the tool.")

    function_schema = models.JSONField(default=dict, blank=True, help_text="JSON schema defining the tool's input parameters.")

    implementation_module = models.CharField(max_length=255, blank=True, help_text="Python module path where the tool's function is implemented.")
    implementation_class = models.CharField(max_length=255, blank=True, help_text="Class name if the tool function is within a class.")

    is_active = models.BooleanField(default=True, help_text="Whether the tool is active and can be used by agents.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name