from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentViewSet

# Create a router for the agents app
router = DefaultRouter()
router.register(r'', AgentViewSet, basename='agent')

# The urlpatterns variable is what Django looks for
urlpatterns = [
    path('', include(router.urls)),
]
