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

    def serialize(self, save=False):
        """
        Serialize the graph structure for frontend rendering.

        Args:
            save: If True, saves the serialized data to graph_data field

        Returns:
            Dictionary with nodes and edges for visualization
        """
        from .services.serializer import GraphSerializer

        if save:
            return GraphSerializer.save_serialized_graph(self)
        return GraphSerializer.serialize_graph(self)

    def get_serialized(self):
        """Get cached serialized data from graph_data, or generate if not present"""
        if 'serialized' in self.graph_data:
            return self.graph_data['serialized']
        return self.serialize(save=True)