from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import ProjectViewSet

# Create a router for the projects app
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

# The urlpatterns variable is what Django looks for
urlpatterns = [
    path('', include(router.urls)),
]