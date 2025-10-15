from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from ..views.auth import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    SignUpView
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='refresh'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify/', TokenVerifyView.as_view(), name='verify'),
]