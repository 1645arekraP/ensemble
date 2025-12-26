from django.shortcuts import render

# apps/credentials/views.py

from rest_framework import viewsets, permissions
from .models import UserCredential
from .serializers import UserCredentialSerializer

class UserCredentialViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the logged-in user to manage their credentials.
    
    Provides full CRUD operations, but is strictly scoped
    to the authenticated user.
    """
    serializer_class = UserCredentialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This is the most important security feature:
        Ensure users can only ever see their OWN credentials.
        """
        return UserCredential.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically associate the new credential with the
        logged-in user.
        """
        serializer.save(user=self.request.user)