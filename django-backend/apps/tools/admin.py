from django.contrib import admin
from .models import Tool

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('name', 'tool_type', 'is_active', 'created_at')
    list_filter = ('tool_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'tool_type')
        }),
        ('Implementation Details', {
            'fields': ('implementation_module', 'implementation_class')
        }),
        ('Configuration', {
            'fields': ('configuration', 'function_schema')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        })
    )
