from django.contrib import admin
from .models import Graph

@admin.register(Graph)
class GraphAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'description')
    list_filter = ('owner',)
    search_fields = ('name', 'description')
    
    def get_queryset(self, request):
        # Optimize query by selecting related owner
        return super().get_queryset(request).select_related('owner')
