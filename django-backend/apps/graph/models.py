from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

class Graph(models.Model):
    """
    Represents a single project or workflow graph.
    The 'graph_data' field is the source of truth for its structure.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='graphs')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    graph_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('owner', 'name')

    def __str__(self):
        return self.name