from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    SignUpView
)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('verify/', TokenVerifyView.as_view(), name='verify'),
]