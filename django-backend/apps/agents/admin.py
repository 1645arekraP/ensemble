from django.contrib import admin
from .models import Agent

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'role', 'provider', 'model', 'created_at')
    list_filter = ('role', 'provider', 'project')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tools',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'project')
        }),
        ('Role & Configuration', {
            'fields': ('role', 'system_instruction_prompt', 'metadata')
        }),
        ('Provider Settings', {
            'fields': ('provider', 'model', 'api_key')
        }),
        ('Tools', {
            'fields': ('tools',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
