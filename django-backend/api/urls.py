from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import GoogleConnectView, GoogleCallbackView
from apps.users.views import *

router = DefaultRouter() # Dynamically creates routes for CRUD operations

urlpatterns = [
    path('auth/', include('apps.users.urls.auth')), # Not CRUD opertions. Only POST to these endpoints so no need for a router.
    path('', include(router.urls)),
    path('graphs/', include('apps.graph.urls')),
    path('agents/', include('apps.agents.urls')),
    path('users/', include('apps.users.urls.users')),
    path('executions/', include('apps.executions.urls')),
    path('tools/', include('apps.tools.urls')),
    path('credentials/', include('apps.credentials.urls')),

    path('auth/google/connect/', GoogleConnectView.as_view(), name='google-connect'),
    path('auth/google/callback/', GoogleCallbackView.as_view(), name='google-callback'),
]