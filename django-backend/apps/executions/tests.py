from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.graph.models import Graph
from apps.executions.models import ExecutionLog
from apps.graph.services.runner import GraphRunner
from unittest.mock import MagicMock, patch
import json

User = get_user_model()

from rest_framework.test import APIClient

class ExecutionLogTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.graph = Graph.objects.create(
            owner=self.user,
            name="Test Graph",
            graph_data={"nodes": [], "edges": []}
        )

    @patch('apps.graph.services.runner.GraphCompiler.compile_graph')
    def test_run_graph_stream_creates_execution_log(self, mock_compile):
        # Mock the compiled graph stream
        mock_compiled_graph = MagicMock()
        mock_compiled_graph.stream.return_value = [
            {'node1': {'current_task': 'Task output', 'messages': []}}
        ]
        mock_compile.return_value = mock_compiled_graph

        runner = GraphRunner()
        stream = runner.run_graph_stream(self.graph, "initial input", user=self.user)
        
        # Consume the stream
        for _ in stream:
            pass

        # Check if ExecutionLog was created
        execution = ExecutionLog.objects.first()
        self.assertIsNotNone(execution)
        self.assertEqual(execution.graph, self.graph)
        self.assertEqual(execution.user, self.user)
        self.assertEqual(execution.status, 'completed')
        self.assertEqual(execution.initial_input, {"input": "initial input"})
        
        # Check logs
        self.assertTrue(len(execution.logs) > 0)
        tool_outputs = [log for log in execution.logs if log.get('type') == 'tool_output']
        self.assertEqual(len(tool_outputs), 1)
        self.assertEqual(tool_outputs[0]['output'], 'Task output')

    def test_execution_log_api(self):
        # Create a dummy execution log
        ExecutionLog.objects.create(
            graph=self.graph,
            user=self.user,
            status='completed',
            logs=[{'type': 'test', 'message': 'hello'}],
            initial_input={"input": "test"}
        )

        response = self.client.get(f'/api/executions/?graph_id={self.graph.id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'completed')
        self.assertEqual(response.data[0]['logs'][0]['message'], 'hello')
