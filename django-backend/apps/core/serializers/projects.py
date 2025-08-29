from rest_framework import serializers
from ..models import Project
from apps.users.serializers import UserSerializer

class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for the Project model."""
    
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'graph_data', 'created_at', 'owner']
        read_only_fields = ['id', 'created_at']