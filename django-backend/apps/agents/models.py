from django.db import models
from ..tools.models import Tool
from ..graph.models import Graph

class Agent(models.Model):
    """Represents a single, configurable agent node within a project."""
    
    # --- Enums for choices ---
    class AgentProvider(models.TextChoices):
        OPENAI = 'openai', 'OpenAI'
        ANTHROPIC = 'anthropic', 'Anthropic'
        GOOGLE = 'google', 'Google'
        CUSTOM = 'custom', 'Custom'

    class AgentRole(models.TextChoices):
        GENERAL = 'general', 'General'
        SUPERVISOR = 'supervisor', 'Supervisor'
        # We can add more roles here

    # --- Core Fields ---
    project = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name='agents')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="A description of the agent's role and capabilities.")
    system_instruction_prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Role and Metadata for Flexibility ---
    role = models.CharField(max_length=50, choices=AgentRole.choices, default=AgentRole.GENERAL)
    metadata = models.JSONField(default=dict, blank=True, help_text="Flexible JSON field for role-specific data.")

    # --- Model Configuration ---
    provider = models.CharField(max_length=50, choices=AgentProvider.choices, default=AgentProvider.OPENAI)
    model = models.CharField(max_length=100, default='gpt-4o', help_text="e.g., 'gpt-4o', 'claude-3-opus-20240229'")
    
    # Encrypt API keys in production
    api_key = models.CharField(max_length=255, blank=True, help_text="API key for the agent's provider. Leave blank to use environment variables.")
    
    # --- Associated Tools ---
    tools = models.ManyToManyField(Tool, blank=True, related_name='agents')

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) in '{self.project.name}'"
