from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter() # Dynamically creates routes for CRUD operations

urlpatterns = [
    path('auth/', include('apps.users.urls.auth')), # Not CRUD opertions. Only POST to these endpoints so no need for a router.
    path('', include(router.urls)),
]