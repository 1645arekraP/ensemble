import os
import logging
from django.conf import settings
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import google_auth_oauthlib.flow
from apps.credentials.models import UserCredential, Tool, encrypt_secret, OAuthState
from apps.users.models import User # Or from django.contrib.auth import get_user_model; User = get_user_model()

logger = logging.getLogger(__name__)


# This assumes client_secret.json is in your django-backend root
CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, 'client_secret.json')

# Define the scopes your app needs
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'openid'
]

# --- VIEWS ---

class GoogleConnectView(APIView):
    """
    Generates a Google OAuth URL and saves the state token
    to the database, linked to the user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES
            )
            flow.redirect_uri = request.build_absolute_uri('/api/auth/google/callback/')
            
            authorization_url, state = flow.authorization_url(
                access_type='offline', 
                prompt='consent'
            )
            
            # Instead of using the session, save the state to the DB
            OAuthState.objects.create(user=request.user, state=state)
            
            return Response({"authorization_url": authorization_url})

        except FileNotFoundError:
            logger.error(f"FATAL: client_secret.json not found at {CLIENT_SECRETS_FILE}")
            return Response({"error": "Server configuration error."}, status=500)
        except Exception as e:
            logger.error(f"Error in GoogleConnectView: {e}")
            return Response({"error": "Failed to initiate Google OAuth flow."}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleCallbackView(APIView):
    """
    Handles the callback from Google. Verifies the 'state' token
    against the database to find the user.
    """
    permission_classes = [AllowAny]
    authentication_classes = [] 

    def get(self, request, *args, **kwargs):
        state = request.GET.get('state')

        try:
            oauth_state_obj = OAuthState.objects.get(state=state)
            user = oauth_state_obj.user
            oauth_state_obj.delete()
            
        except OAuthState.DoesNotExist:
            logger.warning(f"Invalid or expired OAuth state token received: {state}")
            return redirect(f'{settings.FRONTEND_URL}/dashboard/connections?error=invalid_state')
        
        try:
            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES, 
                state=state
            )
            flow.redirect_uri = request.build_absolute_uri('/api/auth/google/callback/')

            code = request.GET.get('code')
            if not code:
                return redirect(f'{settings.FRONTEND_URL}/dashboard/connections?error=no_code_provided')

            flow.fetch_token(code=code)
            creds = flow.credentials
            
            UserCredential.objects.update_or_create(
                user=user,
                credential_type=Tool.ToolType.GMAIL,
                defaults={
                    'encrypted_access_token': encrypt_secret(creds.token),
                    'encrypted_refresh_token': encrypt_secret(creds.refresh_token),
                    'expires_at': creds.expiry,
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to fetch token or save credential for user {user.id}: {e}")
            return redirect(f'{settings.FRONTEND_URL}/dashboard/connections?error=token_fetch_failed')

        return redirect(f'{settings.FRONTEND_URL}/dashboard/connections?success=true')
