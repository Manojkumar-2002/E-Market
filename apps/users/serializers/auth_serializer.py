from django.contrib.auth import authenticate
from rest_framework import serializers
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Standard output serializer for User profile data core responses.
    """
    class Meta:
        model = User
        fields = [
            'id', 
            'email', 
            'first_name', 
            'last_name', 
            'phone_number', 
            'is_staff', 
            'created_at', 
            'updated_at'
        ]
        # Ensure security fields and internal parameters cannot be written via API mutations
        read_only_fields = ['id', 'is_staff', 'created_at', 'updated_at']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles user creation requests, enforces password hashing, 
    and validates payload structures.
    """
    # Write-only constraint ensures passwords never leak out in subsequent GET requests
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'phone_number']
        read_only_fields = ['id']

    def validate_email(self, value):
        """Normalize and enforce unique constraints cleanly at runtime."""
        email_normalized = value.lower().strip()
        if User.objects.filter(email=email_normalized).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email_normalized

    def create(self, validated_data):
        """Passes validated items directly down to your Custom UserManager."""
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Standard clean validation serializer for processing authentication actions.
    Inherits from serializers.Serializer because it does not directly mutate model rows.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True, 
        style={'input_type': 'password'}
    )
    # Marks internal fields to safely bind processed items to the validation scope
    user = serializers.SerializerMethodField()

    class Meta:
        fields = ['email', 'password', 'user']

    def validate(self, attrs):
        """Verifies operational login credentials cleanly through Django auth."""
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials.",
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")

        else:
            raise serializers.ValidationError("Must include both 'email' and 'password'.")

        # Stash the authenticated user entity inside the validated data dict context
        attrs['user'] = user
        return attrs
    

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, help_text="The refresh token to blacklist.")