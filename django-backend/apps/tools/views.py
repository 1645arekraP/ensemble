# apps/tools/views.py
from django.db.models import Q
from rest_framework import viewsets, permissions
from .models import Tool
from .serializers import ToolSerializer

class ToolViewSet(viewsets.ModelViewSet):
    """
    A full CRUD endpoint for managing Tools.
    
    All operations are strictly scoped to the authenticated user.
    """
    
    serializer_class = ToolSerializer
    permission_classes = [permissions.IsAuthenticated] 

    def get_queryset(self):
        """
        This is the most important security feature:
        Ensure users can only ever list, retrieve, update, or delete
        their OWN tools.
        """
        user = self.request.user
        return Tool.objects.filter(
            (Q(user=user) | Q(user__isnull=True)),
            is_active=True
        )

    def perform_create(self, serializer):
        """
        Automatically associate the new tool with the logged-in user
        who is creating it.
        """
        serializer.save(user=self.request.user)