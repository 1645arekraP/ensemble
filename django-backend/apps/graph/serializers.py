from rest_framework import serializers
from .models import Graph
from apps.users.serializers import UserSerializer

class GraphSerializer(serializers.ModelSerializer):
    """Serializer for the Graph model."""

    owner = UserSerializer(read_only=True)

    class Meta:
        model = Graph
        fields = ['id', 'name', 'description', 'graph_data', 'owner']
        read_only_fields = ['id', 'created_at']


class GraphGenerateSerializer(serializers.Serializer):
    """
    Validates the incoming prompt for the graph generator.
    """
    prompt = serializers.CharField(
        max_length=1000, 
        help_text="The natural language prompt describing the workflow."
    )

    current_graph_data = serializers.JSONField(
        required=False, 
        default=dict
    )