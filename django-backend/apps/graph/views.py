from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from .models import Graph
#from .serializers import GraphSerializer


from rest_framework import serializers
from .models import Graph
from apps.users.serializers import UserSerializer

class GraphSerializer(serializers.ModelSerializer):
    """Serializer for the Graph model with visualization support."""

    owner = UserSerializer(read_only=True)
    serialized_graph = serializers.SerializerMethodField()

    class Meta:
        model = Graph
        fields = ['id', 'name', 'description', 'graph_data', 'serialized_graph', 'owner']
        read_only_fields = ['id', 'created_at']

    def get_serialized_graph(self, obj):
        """
        Returns the serialized graph structure for frontend visualization.
        This includes nodes (agents) and edges (connections).
        """
        return obj.get_serialized()

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