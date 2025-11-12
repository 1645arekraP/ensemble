from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentGenerateConfigView, AgentViewSet


router = DefaultRouter()
router.register(r'', AgentViewSet, basename='agent')

urlpatterns = [
    path('generate-config/', AgentGenerateConfigView.as_view(), name='agent-generate-config'),
    path('', include(router.urls)),
]
