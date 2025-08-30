import uuid
from django.db import models
from django.conf import settings

# Enums for choice
class AgentProvider(models.TextChoices):
        OPENAI = 'openai', 'OpenAI'
        ANTHROPIC = 'anthropic', 'Anthropic'
        GOOGLE = 'google', 'Google'

class AgentRole(models.TextChoices):
    GENERAL = 'general', 'General'
    SUPERVISOR = 'supervisor', 'Supervisor'
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

    name = models.CharField(max_length=100)
    description = models.TextField()
    tool_type = models.CharField(max_length=20, choices=ToolType.choices, default=ToolType.BUILT_IN)
    
    # For BUILT_IN tools: stores the Python import path
    path = models.CharField(max_length=255, blank=True, null=True, help_text="Import path for Built-in tools'")
    
    # For API tools: stores the endpoint configuration
    api_config = models.JSONField(default=dict, blank=True, help_text="Configuration for API tools (URL, method, headers, etc.)")

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_tools'
    )

    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='owned_tools',
        blank=True
    )

    is_public = models.BooleanField(default=False, help_text="If true, this tool is available to all users.")


    def __str__(self):
        return f"{self.name} ({self.get_tool_type_display()})"


class AgentTemplate(BaseModel):    
    # --- Ownership and Visibility ---
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_agent_templates'
    )

    # ADDED: ManyToManyField for multiple owners
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='owned_agent_templates',
        blank=True
    )
    
    is_public = models.BooleanField(default=False, help_text="If true, this agent template is available to all users.")
    
    # --- Core Definition Fields ---
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    system_instruction_prompt = models.TextField()
    role = models.CharField(max_length=50, choices=AgentRole.choices, default=AgentRole.GENERAL)
    provider = models.CharField(max_length=50, choices=AgentProvider.choices, default=AgentProvider.OPENAI)
    model = models.CharField(max_length=100, default='gpt-4o')
    tools = models.ManyToManyField(Tool, blank=True, related_name='agent_templates')
    
    def __str__(self):
        return self.name

class Agent(BaseModel):
    # This model represents an AgentTemplate used *within* a Project.
    # It can be configured with project-specific overrides.
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='agents')
    template = models.ForeignKey(AgentTemplate, on_delete=models.SET_NULL, null=True, blank=True, help_text="The template this agent was created from.")
    
    # Fields can be copied from the template and overridden here
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    system_instruction_prompt = models.TextField()
    role = models.CharField(max_length=50, choices=AgentRole.choices, default=AgentRole.GENERAL)
    provider = models.CharField(max_length=50, choices=AgentProvider.choices, default=AgentProvider.OPENAI)
    model = models.CharField(max_length=100, default='gpt-4o')
    tools = models.ManyToManyField(Tool, blank=True, related_name='agents')
    api_key = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Project-specific API key. Leave blank to use environment variables."
    )
    
    # This is for data specific to this agent's position/state on the canvas
    metadata = models.JSONField(default=dict, blank=True, help_text="Project-specific data, e.g., node position on the canvas.")

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.name} in '{self.project.name}'"
