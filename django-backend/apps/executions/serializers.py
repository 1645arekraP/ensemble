from rest_framework import serializers
from apps.executions.models import ExecutionLog

class RunInputSerializer(serializers.Serializer):
    """
    Serializes the input for a graph run.
    This just validates the POST data from the user.
    """
    input = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="The user's initial input message to start the graph execution."
    )

class ExecutionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionLog
        fields = ['id', 'graph', 'user', 'status', 'started_at', 'completed_at', 'final_output', 'logs', 'initial_input']
        read_only_fields = ['id', 'started_at', 'completed_at', 'logs']