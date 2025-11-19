from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials as GoogleCredentials
from apps.credentials.models import UserCredential, Tool, encrypt_secret
import google_auth_oauthlib.flow
import google.oauth2.credentials
import os

# Create your views here.
class GoogleConnectView(APIView):
    """
    Redirects the user to Google's OAuth 2.0 consent page.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/gmail.readonly',
            ]
        )
        
        # This must match the one in your Google Cloud Console
        flow.redirect_uri = request.build_absolute_uri('/api/auth/google/callback/')
        
        # Generate the URL and send the user there
        authorization_url, state = flow.authorization_url(access_type='offline', prompt='consent')
        
        # Save the state in the session so we can verify it in the callback
        request.session['oauth_state'] = state
        
        return redirect(authorization_url)


# This is the view for STEPS 4, 5, 6
class GoogleCallbackView(APIView):
    """
    Handles the callback from Google after user consent.
    Exchanges the code for tokens and saves them.
    """
    def get(self, request, *args, **kwargs):
        # Verify the state to prevent CSRF attacks
        state = request.GET.get('state')
        if not state or state != request.session.get('oauth_state'):
            return redirect(f'{settings.FRONTEND_URL}/connections?error=invalid_state')

        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=None, # Scopes are not needed for the fetch_token part
            state=state
        )
        flow.redirect_uri = request.build_absolute_uri('/api/auth/google/callback/')

        # Use the code from the request to fetch the tokens
        code = request.GET.get('code')
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
        except Exception as e:
            return redirect(f'{settings.FRONTEND_URL}/connections?error=token_fetch_failed')

        # Now, save these tokens to your UserCredential model
        UserCredential.objects.update_or_create(
            user=request.user,
            credential_type=Tool.ToolType.GMAIL, # You need to add GMAIL to your ToolType enum
            defaults={
                'encrypted_access_token': encrypt_secret(creds.token),
                'encrypted_refresh_token': encrypt_secret(creds.refresh_token),
                'expires_at': creds.expiry,
            }
        )

        # 7. Redirect back to the frontend
        return redirect(f'{settings.FRONTEND_URL}/connections?success=true')