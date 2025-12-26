from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.graph.models import Graph
from apps.graph.services.runner import GraphRunner
from .serializers import RunInputSerializer
import json

from rest_framework.permissions import IsAuthenticated

class ProjectRunStreamView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Handles the streaming execution of a saved project graph using SSE.
    """
    def post(self, request, project_id):
        # Validate the incoming input
        serializer = RunInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_input = serializer.validated_data['input']

        # Get the saved graph
        try:
            graph = Graph.objects.get(id=project_id, owner=request.user) 
        except Graph.DoesNotExist:
            return Response({"error": "Graph project not found"}, status=status.HTTP_404_NOT_FOUND)

        # Instantiate GraphRunner
        runner = GraphRunner()
        
        # Create the generator
        event_stream = runner.run_graph_stream(
            graph=graph, 
            initial_input=user_input,
            user=request.user 
        )

        # Return StreamingHttpResponse
        response = StreamingHttpResponse(event_stream, content_type='application/x-ndjson')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no' # Disable buffering in Nginx if used
        return response
