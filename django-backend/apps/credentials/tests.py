from django.test import TestCase
from unittest.mock import patch, MagicMock
from google.auth.exceptions import RefreshError
from .models import UserCredential, Tool, encrypt_secret
from .services import refresh_google_token
from django.contrib.auth import get_user_model

User = get_user_model()

class GoogleTokenRefreshTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.credential = UserCredential.objects.create(
            user=self.user,
            credential_type=Tool.ToolType.GMAIL,
            encrypted_access_token=encrypt_secret('fake_access_token'),
            encrypted_refresh_token=encrypt_secret('fake_refresh_token')
        )

    @patch('apps.credentials.services.Credentials')
    def test_refresh_google_token_invalid_grant(self, mock_credentials_cls):
        # Setup mock to raise RefreshError
        mock_creds_instance = MagicMock()
        mock_creds_instance.refresh.side_effect = RefreshError('invalid_grant: Token has been expired or revoked.')
        mock_credentials_cls.return_value = mock_creds_instance

        # Verify that the exception is raised (currently it re-raises generic Exception)
        # After fix, it should raise a specific error and delete the credential
        
        with self.assertRaises(Exception) as cm:
            refresh_google_token(self.credential)
        
        # Check if credential was deleted
        self.assertFalse(UserCredential.objects.filter(id=self.credential.id).exists())
        self.assertIn("Google token expired or revoked", str(cm.exception))
        print(f"\nCaught expected exception: {cm.exception}")
