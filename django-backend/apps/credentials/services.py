import logging
from django.conf import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .models import UserCredential, encrypt_secret, decrypt_secret

logger = logging.getLogger(__name__)

def refresh_google_token(credential: UserCredential) -> Credentials:
    """
    Refreshes an expired Google OAuth token and saves the new one.
    Returns valid, usable credentials.
    """
    logger.info(f"Refreshing Google token for user {credential.user_id}...")
    
    # Rebuild the credentials object from stored tokens
    creds = Credentials(
        token=decrypt_secret(credential.encrypted_access_token),
        refresh_token=decrypt_secret(credential.encrypted_refresh_token),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
    )

    try:
        # The refresh() method checks expiry and refreshes if needed
        creds.refresh(Request())
        
        # Save the new, refreshed tokens back to the database
        credential.encrypted_access_token = encrypt_secret(creds.token)
        if creds.refresh_token:
             # Google might issue a new refresh token
            credential.encrypted_refresh_token = encrypt_secret(creds.refresh_token)
        credential.expires_at = creds.expiry
        credential.save()
        
        logger.info(f"Successfully refreshed token for user {credential.user_id}")
        return creds
        
    except Exception as e:
        logger.error(f"Failed to refresh Google token for user {credential.user_id}: {e}")
        # This will fail the tool run, which is correct
        raise Exception(f"Failed to refresh Google token: {e}")