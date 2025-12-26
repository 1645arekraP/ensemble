from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Graph
from apps.tools.models import Tool
from apps.credentials.models import UserCredential, encrypt_secret
from unittest.mock import patch, MagicMock
import json

User = get_user_model()

class GraphValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.tool = Tool.objects.create(
            name='gmail_tool',
            tool_type=Tool.ToolType.GMAIL,
            description='A tool to read emails'
        )
        
        self.graph = Graph.objects.create(
            owner=self.user,
            name='Test Graph',
            graph_data={
                'nodes': [
                    {
                        'id': 'tool_node_1',
                        'type': 'tool',
                        'data': {'id': self.tool.id, 'label': 'Gmail Tool'}
                    }
                ]
            }
        )

    def test_validate_missing_credential(self):
        response = self.client.get(f'/api/graphs/{self.graph.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['valid'])
        self.assertIn('Missing credential', response.data['errors'][0])

    def test_validate_valid_credential(self):
        UserCredential.objects.create(
            user=self.user,
            credential_type=Tool.ToolType.GMAIL,
            encrypted_access_token=encrypt_secret('token'),
            encrypted_refresh_token=encrypt_secret('refresh')
        )
        
        response = self.client.get(f'/api/graphs/{self.graph.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertEqual(len(response.data['errors']), 0)

    @patch('apps.graph.services.runner.GraphCompiler.compile_graph')
    def test_run_graph_stream_tool_output(self, mock_compile):
        from apps.graph.services.runner import GraphRunner
        
        # Mock the compiled graph stream to yield a tool output state
        mock_compiled_graph = MagicMock()
        mock_compiled_graph.stream.return_value = [
            {'tool_node_1': {'current_task': 'Tool executed successfully', 'messages': []}}
        ]
        mock_compile.return_value = mock_compiled_graph
        
        runner = GraphRunner()
        stream = runner.run_graph_stream(self.graph, "test input", user=self.user)
        
        # Consume stream and check for tool_output event
        events = []
        for chunk in stream:
            events.append(json.loads(chunk))
            
        tool_outputs = [e for e in events if e.get('type') == 'tool_output']
        self.assertEqual(len(tool_outputs), 1)
        self.assertEqual(tool_outputs[0]['output'], 'Tool executed successfully')
        self.assertEqual(tool_outputs[0]['node'], 'tool_node_1')
