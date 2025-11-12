from django.contrib import admin
from .models import Agent

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):

    list_display = ('name', 'user', 'role', 'provider', 'model', 'created_at')
    

    list_filter = ('role', 'provider', 'user')
    

    search_fields = ('name', 'description', 'user__email')
    
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tools',)
    
    fieldsets = (
        ('Basic Information', {
  
            'fields': ('name', 'description', 'user')
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