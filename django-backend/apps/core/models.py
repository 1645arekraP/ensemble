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
    """
    Defines a tool that an agent can use. The actual Python function is implemented
    separately in your agent logic.
    """
    name = models.CharField(max_length=100, unique=True, help_text="The function name for the tool.")
    description = models.TextField(help_text="Description for the LLM to understand the tool's purpose.")

    def __str__(self):
        return self.name

class Agent(BaseModel):
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
