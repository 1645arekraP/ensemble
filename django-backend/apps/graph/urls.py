from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GraphGenerateView, GraphViewSet
from ..executions.views import ProjectRunView
from ..executions.views_stream import ProjectRunStreamView

# Create a router for the projects app
router = DefaultRouter()
router.register(r'', GraphViewSet, basename='graph')

# The urlpatterns variable is what Django looks for
urlpatterns = [
    path('<str:project_id>/run/', ProjectRunView.as_view(), name='project-run'),
    path('<str:project_id>/stream/', ProjectRunStreamView.as_view(), name='project-run-stream'),
    path('generate/', GraphGenerateView.as_view(), name='graph-generate'),
    path('', include(router.urls)),
]