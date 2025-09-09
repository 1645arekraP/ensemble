from django.db import models
from django.contrib.auth import get_user_model

class Graph(models.Model):
    """Represents a multi-agent orchestration project/canvas."""
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='graphs')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    graph_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name