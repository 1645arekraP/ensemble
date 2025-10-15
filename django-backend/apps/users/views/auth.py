# views.py
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers.auth import SignUpSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings

from rest_framework import generics

class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom Login View to set the refresh token in an HttpOnly cookie.
    """
    def post(self, request, *args, **kwargs):
        
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            refresh_token = response.data.get('refresh')
            
            if refresh_token:
                is_secure = settings.SECURE_SSL_REDIRECT if hasattr(settings, 'SECURE_SSL_REDIRECT') else False
                response.set_cookie(
                    key='refresh',
                    value=refresh_token,
                    httponly=True,
                    samesite='Lax', # Use 'None' for production (HTTPS)
                    secure=is_secure, # Use True for production
                    path='/'
                )

                del response.data['refresh']

        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom Refresh View to read the refresh token from the cookie
    and set the new one.
    """
    def post(self, request, *args, **kwargs):
        
        refresh_token = request.COOKIES.get('refresh')

        if refresh_token:
            
            request.data['refresh'] = refresh_token

        
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            
            new_refresh_token = response.data.get('refresh')
            if new_refresh_token:
                is_secure = settings.SECURE_SSL_REDIRECT if hasattr(settings, 'SECURE_SSL_REDIRECT') else False
                response.set_cookie(
                    key='refresh',
                    value=new_refresh_token,
                    httponly=True,
                    samesite='Lax', # Use 'None' for production (HTTPS)
                    secure=is_secure, # Use True for production
                    path='/'
                )
                del response.data['refresh']
        
        return response