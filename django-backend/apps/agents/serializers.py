from rest_framework import serializers
from .models import Agent
from apps.tools.models import Tool


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for Agent model with tool support."""

    tools = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tool.objects.all(),
        required=False
    )

    class Meta:
        model = Agent
        fields = [
            'id',
            'project',
            'name',
            'description',
            'system_instruction_prompt',
            'role',
            'provider',
            'model',
            'api_key',
            'tools',
            'metadata',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Custom validation for agent creation."""
        # Ensure unique name within project
        project = data.get('project')
        name = data.get('name')

        if project and name:
            # Check if updating existing agent
            if self.instance:
                # Exclude current instance from uniqueness check
                if Agent.objects.filter(
                    project=project,
                    name=name
                ).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError({
                        'name': 'An agent with this name already exists in this project.'
                    })
            else:
                # Creating new agent
                if Agent.objects.filter(project=project, name=name).exists():
                    raise serializers.ValidationError({
                        'name': 'An agent with this name already exists in this project.'
                    })

        return data


class AgentDetailSerializer(AgentSerializer):
    """Extended serializer with full tool details."""

    from apps.tools.serializers import ToolSerializer
    tools = ToolSerializer(many=True, read_only=True)
