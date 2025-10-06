from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GraphViewSet

# Create a router for the projects app
router = DefaultRouter()
router.register(r'', GraphViewSet, basename='graph')

# The urlpatterns variable is what Django looks for
urlpatterns = [
    path('', include(router.urls)),
]