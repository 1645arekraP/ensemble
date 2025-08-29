# projects/views.py

from rest_framework import viewsets, permissions
from ..models import Project
from ..serializers import ProjectSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    # Ensure only authenticated users can access this endpoint.
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the projects
        for the currently authenticated user.
        """
        return Project.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        Assign the owner of the project to the currently logged-in user.
        This is the crucial step for automatically setting the owner.
        """
        serializer.save(owner=self.request.user)