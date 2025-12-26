from rest_framework import serializers
from .models import Tool

class ToolSerializer(serializers.ModelSerializer):
    """
    Serializes the Tool model for full CRUD operations.
    - 'user' is set automatically from the view and is read-only.
    - 'config' is write-only for security (don't send secrets back).
    """
    
    tool_type_display = serializers.CharField(source='get_tool_type_display', read_only=True)
    
    user = serializers.StringRelatedField(read_only=True)

    config = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Tool
        fields = [
            'id', 
            'user',
            'name', 
            'description', 
            'tool_type', 
            'tool_type_display',
            'config', 
            'is_active',
            'created_at',
        ]
        
        read_only_fields = ['id', 'user', 'tool_type_display', 'created_at']