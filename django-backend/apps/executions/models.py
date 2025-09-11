from django.db import models
from django.contrib.auth import get_user_model
from ..graph.models import Graph

class ExecutionLog(models.Model):
    """Logs for each execution of a graph."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name='executions')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='executions')

    initial_input = models.JSONField(default=dict, blank=True)
    context = models.JSONField(default=dict, blank=True)
    final_output = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Execution {self.id} of {self.graph.name}"
    
    class Meta:
        ordering = ['-started_at']

class ExecutionStep(models.Model):
    """Logs each step taken by an agent during execution."""
    execution = models.ForeignKey(ExecutionLog, on_delete=models.CASCADE, related_name='steps')

    agent_name = models.CharField(max_length=255)
    input_data = models.TextField()
    output_data = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Step {self.id} by {self.agent_name} in Execution {self.execution.id}"
    
    class Meta:
        ordering = ['executed_at']