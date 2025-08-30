from django.contrib import admin
from .models import Project, Tool, Agent, AgentTemplate

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Configuration for the Project model in the admin interface."""
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__email')
    list_filter = ('owner',)
    ordering = ('-created_at',)

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    """Configuration for the Tool model in the admin interface."""
    list_display = ('name', 'tool_type', 'path')
    search_fields = ('name', 'description')
    list_filter = ('tool_type',)
    ordering = ('name',)
    filter_horizontal = ('owners',)

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Configuration for the Agent model in the admin interface."""
    list_display = ('name', 'project', 'role', 'provider', 'model')
    search_fields = ('name', 'project__name')
    list_filter = ('project', 'role', 'provider')
    ordering = ('project', 'name')

@admin.register(AgentTemplate)
class AgentTemplateAdmin(admin.ModelAdmin):
    """Configuration for the Agent model in the admin interface."""
    list_display = ('name', 'creator', 'role', 'provider', 'model')
    search_fields = ('name',)
    list_filter = ('role', 'provider')
    ordering = ('name',)
    filter_horizontal = ('owners', 'tools',)
