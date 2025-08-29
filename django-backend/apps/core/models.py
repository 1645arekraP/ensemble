import uuid
from django.db import models
from django.conf import settings


# --- Abstract Base Model ---

class BaseModel(models.Model):
    """An abstract base model with UUID primary keys and timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# --- Concrete Models ---

class Project(BaseModel):
    """Represents a multi-agent orchestration project/canvas."""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    graph_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

class Tool(BaseModel):
    """Defines a tool that an agent can use, supporting both built-in and external API tools."""
    class ToolType(models.TextChoices):
        BUILT_IN = 'BUILT_IN', 'Built-in Tool'
        API = 'API', 'API Tool'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    tool_type = models.CharField(max_length=20, choices=ToolType.choices, default=ToolType.BUILT_IN)
    
    # For BUILT_IN tools: stores the Python import path
    path = models.CharField(max_length=255, blank=True, null=True, help_text="Import path for Built-in tools'")
    
    # For API tools: stores the endpoint configuration
    api_config = models.JSONField(default=dict, blank=True, help_text="Configuration for API tools (URL, method, headers, etc.)")

    def __str__(self):
        return f"{self.name} ({self.get_tool_type_display()})"

class Agent(BaseModel):
    """Represents a single, configurable agent node within a project."""
    
    # --- Enums for choices ---
    class AgentProvider(models.TextChoices):
        OPENAI = 'openai', 'OpenAI'
        ANTHROPIC = 'anthropic', 'Anthropic'
        GOOGLE = 'google', 'Google'

    class AgentRole(models.TextChoices):
        GENERAL = 'general', 'General'
        SUPERVISOR = 'supervisor', 'Supervisor'
        # We can add more roles here

    # --- Core Fields ---
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='agents')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="A description of the agent's role and capabilities.")
    system_instruction_prompt = models.TextField()

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
