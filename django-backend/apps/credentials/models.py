import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from cryptography.fernet import Fernet, InvalidToken

from apps.tools.models import Tool

logger = logging.getLogger(__name__)

try:
    if not settings.CREDENTIALS_ENCRYPTION_KEY:
        raise ValueError("CREDENTIALS_ENCRYPTION_KEY is not set in environment variables.")
    
    # Ensure the key is 32 bytes URL-safe base64-encoded
    key_bytes = settings.CREDENTIALS_ENCRYPTION_KEY.encode('utf-8')
    cipher_suite = Fernet(key_bytes)
    
except (ValueError, TypeError) as e:
    logger.error(f"FATAL: Invalid CREDENTIALS_ENCRYPTION_KEY. {e}")
    # This is a critical failure. 
    cipher_suite = None 

def encrypt_secret(secret: str) -> str:
    """Encrypts a string and returns it as a string."""
    if cipher_suite is None:
        raise ValueError("Encryption cipher is not initialized.")
    return cipher_suite.encrypt(secret.encode('utf-8')).decode('utf-8')

def decrypt_secret(encrypted_secret: str) -> str:
    """Decrypts a string and returns it."""
    if cipher_suite is None:
        raise ValueError("Encryption cipher is not initialized.")
    try:
        return cipher_suite.decrypt(encrypted_secret.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        logger.error("Failed to decrypt secret: Invalid token or key.")
        raise ValueError("Decryption failed. Invalid token or key.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during decryption: {e}")
        raise

class UserCredential(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    credential_type = models.CharField(
        max_length=50, 
        choices=Tool.ToolType.choices 
    )
    
    # Store the encrypted access token 
    encrypted_access_token = models.TextField()
    
    # Store the encrypted refresh token (long-lived, or permanent)
    encrypted_refresh_token = models.TextField(blank=True, null=True) # Not all OAuth flows provide this
    
    # Store when the access token expires
    expires_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A user can only have one credential for each tool type
        unique_together = ('user', 'credential_type')

    def __str__(self):
        return f"{self.user.username}'s Credential for {self.get_credential_type_display()}"
    
    def is_expired(self) -> bool:
        """Checks if the access token is expired."""
        if not self.expires_at:
            return False # Can't expire if we don't know when
        # Give a 60-second buffer
        return self.expires_at <= (timezone.now() + timezone.timedelta(seconds=60))

    def refresh_token(self):
        """
        A placeholder for the logic to refresh the token.
        """
        pass 


class OAuthState(models.Model):
    """
    A temporary, one-time-use token to securely link a user
    to an OAuth flow.
    """
    state = models.CharField(max_length=128, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OAuthState for {self.user.username}"