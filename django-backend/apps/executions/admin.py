from django.contrib import admin
from .models import ExecutionLog, ExecutionStep

class ExecutionStepInline(admin.TabularInline):
    model = ExecutionStep
    extra = 0
    readonly_fields = ('executed_at',)
    fields = ('agent_name', 'input_data', 'output_data', 'executed_at')
    can_delete = False
    max_num = 0  # Prevents adding new steps through admin
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'graph', 'user', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'graph', 'user', 'started_at')
    search_fields = ('graph__name', 'user__email', 'final_output')
    readonly_fields = ('started_at', 'completed_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('graph', 'user', 'status')
        }),
        ('Input/Output', {
            'fields': ('initial_input', 'final_output')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': ('context',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ExecutionStepInline]
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of execution logs

@admin.register(ExecutionStep)
class ExecutionStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'execution', 'agent_name', 'executed_at')
    list_filter = ('agent_name', 'executed_at', 'execution__status')
    search_fields = ('agent_name', 'input_data', 'output_data')
    readonly_fields = ('executed_at',)
    
    fieldsets = (
        ('Execution Information', {
            'fields': ('execution', 'agent_name')
        }),
        ('Step Data', {
            'fields': ('input_data', 'output_data')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('executed_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of execution steps
