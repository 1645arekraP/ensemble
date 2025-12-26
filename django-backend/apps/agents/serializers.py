# apps/agents/serializers.py

from rest_framework import serializers
from .models import Agent

class AgentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Agent model (list and create/update).
    """
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Agent
        fields = [
            'id', 'user', 'name', 'description', 
            'system_instruction_prompt', 'role', 'metadata',
            'provider', 'model', 'api_key', 'tools', 
            'created_at', 'updated_at'
        ]
        
        
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        
        extra_kwargs = {
            'api_key': {'write_only': True, 'required': False}
        }

class AgentDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for the Agent model (retrieve action).
    It's good practice to have a separate one, even if it's
    the same as the base serializer for now.
    """
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Agent
        fields = [
            'id', 'user', 'name', 'description', 
            'system_instruction_prompt', 'role', 'metadata',
            'provider', 'model', 'api_key', 'tools', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True, 'required': False}
        }

class AgentGenerateConfigSerializer(serializers.Serializer):
    """
    Validates the incoming prompt for the agent config generator.
    """
    prompt = serializers.CharField(
        max_length=500, 
        help_text="The natural language prompt describing the agent."
    )