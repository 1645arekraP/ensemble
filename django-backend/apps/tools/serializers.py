from rest_framework import serializers
from .models import Tool


class ToolSerializer(serializers.ModelSerializer):
    """Serializer for Tool model."""

    class Meta:
        model = Tool
        fields = [
            'id',
            'name',
            'description',
            'tool_type',
            'config',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
