from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GraphViewSet
from ..executions.views import ProjectRunView

# Create a router for the projects app
router = DefaultRouter()
router.register(r'', GraphViewSet, basename='graph')

# The urlpatterns variable is what Django looks for
urlpatterns = [
    path('', include(router.urls)),
    path('<str:project_id>/run/', ProjectRunView.as_view(), name='project-run'),
]