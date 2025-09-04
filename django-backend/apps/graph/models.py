from django.db import models
from django.conf import settings

class Graph(models.Model):
    """Represents a multi-agent orchestration project/canvas."""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='graphs')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    graph_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name