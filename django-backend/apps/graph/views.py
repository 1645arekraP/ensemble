from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, views, response, status
from .models import Graph
from .serializers import GraphSerializer, GraphGenerateSerializer
from .services.generator import generate_graph_from_prompt

from rest_framework import serializers
from .models import Graph
from apps.users.serializers import UserSerializer

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