# apps/credentials/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserCredentialViewSet

router = DefaultRouter()
router.register(r'', UserCredentialViewSet, basename='credential')

urlpatterns = [
    path('', include(router.urls)),
]