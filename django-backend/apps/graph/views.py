from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, views, response, status
from .models import Graph
from .serializers import GraphSerializer, GraphGenerateSerializer
from .services.generator import generate_graph_from_prompt

from rest_framework import serializers
from rest_framework.decorators import action
from .models import Graph
from apps.users.serializers import UserSerializer
from apps.tools.models import Tool
from apps.credentials.models import UserCredential
from apps.credentials.services import refresh_google_token
from google.auth.exceptions import RefreshError

class GraphViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """
    queryset = Graph.objects.all()
    serializer_class = GraphSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the projects
        for the currently authenticated user.
        """
        return Graph.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        Assign the owner of the project to the currently logged-in user.
        This is the crucial step for automatically setting the owner.
        """
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['get'])
    def validate(self, request, pk=None):
        """
        Checks if the graph's tools have valid credentials for the current user.
        Returns { "valid": bool, "errors": [str] }
        """
        graph = self.get_object()
        user = request.user
        errors = []

        if not graph.graph_data or 'nodes' not in graph.graph_data:
            return response.Response({"valid": True, "errors": []})

        nodes = graph.graph_data.get('nodes', [])
        for node in nodes:
            if node.get('type') == 'tool':
                tool_data = node.get('data', {})
                tool_db_id = tool_data.get('id')
                
                try:
                    tool = Tool.objects.get(id=tool_db_id)
                    
                    # Check if this tool requires a credential
                    # Currently only GMAIL requires a user-specific credential
                    if tool.tool_type == Tool.ToolType.GMAIL:
                        try:
                            credential = UserCredential.objects.get(
                                user=user,
                                credential_type=Tool.ToolType.GMAIL
                            )
                            
                            # Check expiry and attempt refresh
                            if credential.is_expired():
                                try:
                                    refresh_google_token(credential)
                                except Exception:
                                    # Refresh failed (already handled by service, but we catch here to be safe)
                                    errors.append(f"Credential for {tool.name} is expired and could not be refreshed. Please reconnect.")
                                    
                        except UserCredential.DoesNotExist:
                            errors.append(f"Missing credential for {tool.name}. Please connect your Google account.")
                            
                except Tool.DoesNotExist:
                    # If tool doesn't exist, the graph is invalid anyway, but that's a different error.
                    # We'll ignore it here or flag it.
                    pass

        return response.Response({
            "valid": len(errors) == 0,
            "errors": errors
        })


class GraphGenerateView(views.APIView):
    """
    A view that generates graph_data JSON from a natural
    language prompt using an LLM.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = GraphGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        prompt = serializer.validated_data['prompt']
        current_graph_data = serializer.validated_data['current_graph_data']
        user = request.user

        try:
            generated_json = generate_graph_from_prompt(prompt, user, current_graph_data)
            
            return response.Response(generated_json, status=status.HTTP_200_OK)

        except Exception as e:
            return response.Response(
                {"error": "Failed to generate graph.", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )