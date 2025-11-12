# apps/credentials/serializers.py

from rest_framework import serializers
from .models import UserCredential, encrypt_secret

class UserCredentialSerializer(serializers.ModelSerializer):
    """
    Securely serializes UserCredential objects.
    
    - 'access_token' and 'refresh_token' are WRITE-ONLY. They are used
      to create/update but are NEVER returned.
    - 'credential_type_display' is READ-ONLY for convenience.
    - Encryption is handled inside the .create() and .update() methods.
    """

    # --- Read-Only Fields ---
    credential_type_display = serializers.CharField(
        source='get_credential_type_display', 
        read_only=True
    )
    user = serializers.StringRelatedField(read_only=True)

    # --- Write-Only Fields (for receiving secrets) ---
    access_token = serializers.CharField(
        write_only=True, 
        required=True, 
        help_text="The plain text API key or OAuth access token."
    )
    refresh_token = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_null=True, 
        help_text="The plain text OAuth refresh token, if applicable."
    )

    class Meta:
        model = UserCredential
        
        # These are the fields that are "safe" to return in a GET request.
        # Notice the encrypted fields are NOT listed here.
        fields = [
            'id', 
            'user', 
            'credential_type', 
            'credential_type_display', 
            'expires_at', 
            'created_at',
            
            # Write-only fields
            'access_token',
            'refresh_token',
        ]
        
        # 'credential_type' and 'expires_at' can be set on creation/update.
        # 'user' is set automatically from the request.
        read_only_fields = ('id', 'user', 'credential_type_display', 'created_at')

    def create(self, validated_data):
        """
        Handle creation and encrypt secrets.
        """
        # Pop the plain text secrets from the data
        access_token = validated_data.pop('access_token')
        refresh_token = validated_data.pop('refresh_token', None)
        
        # Add the encrypted versions
        validated_data['encrypted_access_token'] = encrypt_secret(access_token)
        if refresh_token:
            validated_data['encrypted_refresh_token'] = encrypt_secret(refresh_token)

        # Let the default .create() handle the rest
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Handle update and encrypt any new secrets.
        """
        # If a new token/key was provided, encrypt it
        if 'access_token' in validated_data:
            access_token = validated_data.pop('access_token')
            instance.encrypted_access_token = encrypt_secret(access_token)
        
        if 'refresh_token' in validated_data:
            refresh_token = validated_data.pop('refresh_token')
            instance.encrypted_refresh_token = encrypt_secret(refresh_token) if refresh_token else None

        # Let the default .update() handle the other fields (like expires_at)
        return super().update(instance, validated_data)