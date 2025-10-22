from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Agent
from .serializers import AgentSerializer, AgentDetailSerializer


class AgentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing agents.

    list: Get all agents (filtered by user's graphs)
    retrieve: Get a specific agent with full tool details
    create: Create a new agent
    update: Update an agent
    partial_update: Partially update an agent
    destroy: Delete an agent
    """
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter agents to only those in graphs owned by the current user.
        """
        return Agent.objects.filter(project__owner=self.request.user)

    def get_serializer_class(self):
        """Use detailed serializer for retrieve actions."""
        if self.action == 'retrieve':
            return AgentDetailSerializer
        return AgentSerializer

    def perform_create(self, serializer):
        """
        Create a new agent. Ensure the project belongs to the current user.
        """
        project = serializer.validated_data.get('project')

        # Check if user owns the project
        if project.owner != self.request.user:
            raise permissions.PermissionDenied(
                "You can only create agents in your own projects."
            )

        serializer.save()

    def perform_update(self, serializer):
        """
        Update an agent. Ensure the project belongs to the current user.
        """
        if serializer.instance.project.owner != self.request.user:
            raise permissions.PermissionDenied(
                "You can only update agents in your own projects."
            )

        serializer.save()

    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """
        Get all agents for a specific project.
        Query params: project_id
        """
        project_id = request.query_params.get('project_id')

        if not project_id:
            return Response(
                {'error': 'project_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        agents = self.get_queryset().filter(project_id=project_id)
        serializer = self.get_serializer(agents, many=True)
        return Response(serializer.data)
