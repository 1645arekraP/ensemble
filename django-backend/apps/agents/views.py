from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Agent
from .serializers import AgentSerializer, AgentDetailSerializer
from rest_framework import viewsets, permissions, views, response, status
from .serializers import AgentSerializer, AgentGenerateConfigSerializer
from .services.generator import generate_agent_config_from_prompt
from django.db.models import Q

class AgentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing a user's Agent library.

    list: Get all agents owned by the user, plus global system agents.
    retrieve: Get a specific agent.
    create: Create a new agent owned by the user.
    update: Update an agent owned by the user.
    partial_update: Partially update an agent owned by the user.
    destroy: Delete an agent owned by the user.
    """
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all agents
        for the currently authenticated user, PLUS global (system) agents.
        """
        user = self.request.user
        return Agent.objects.filter(
            (Q(user=user) | Q(user__isnull=True))
        )

    def get_serializer_class(self):
        """Use detailed serializer for retrieve actions."""
        if self.action == 'retrieve':
            return AgentDetailSerializer
        return AgentSerializer

    def perform_create(self, serializer):
        """
        Assign the owner of the agent to the currently logged-in user.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Update an agent. Ensure the user owns this agent.
        """
        # Check if the agent being updated is owned by the user
        if serializer.instance.user != self.request.user:
            raise permissions.PermissionDenied(
                "You can only update your own agents."
            )
        serializer.save()

    def perform_destroy(self, instance):
        """
        Delete an agent. Ensure the user owns this agent.
        """
        # Check if the agent being deleted is owned by the user
        if instance.user != self.request.user:
            raise permissions.PermissionDenied(
                "You can only delete your own agents. System agents are protected."
            )
        instance.delete()

class AgentGenerateConfigView(views.APIView):
    """
    A view that generates an Agent's configuration (name, description, prompt)
    from a natural language prompt using an LLM.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AgentGenerateConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        prompt = serializer.validated_data['prompt']
        user = request.user

        try:
            generated_config = generate_agent_config_from_prompt(prompt, user)
            
            return response.Response(generated_config, status=status.HTTP_200_OK)

        except Exception as e:
            return response.Response(
                {"error": "Failed to generate agent configuration.", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )