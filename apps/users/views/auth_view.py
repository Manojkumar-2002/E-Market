from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from apps.core.utils.response_handler import ResponseHandler
from apps.core.utils.serializer_handler import SerializerErrorHandler  
from apps.users.serializers import RegisterSerializer, LoginSerializer, UserSerializer, LogoutSerializer

from apps.carts.utils.guest_to_user_cart import merge_guest_cart_to_user

from drf_spectacular.utils import extend_schema



class RegisterAPIView(APIView):
    """
    Endpoint for creating a new user account inside the marketplace.
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        
        if not serializer.is_valid():
            return ResponseHandler.error_response(
                message=SerializerErrorHandler.get_first_error_message(serializer.errors),
                errors=SerializerErrorHandler.format_errors(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        user = serializer.save()
        response_data = UserSerializer(user).data
        
        return ResponseHandler.success_response(
            message="User registered successfully.",
            data=response_data,
            status_code=status.HTTP_201_CREATED
        )


class LoginAPIView(APIView):
    """
    Endpoint to authenticate users and issue secure stateless JWT access/refresh tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        session_key = request.session.session_key
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return ResponseHandler.error_response(
                message=SerializerErrorHandler.get_first_error_message(serializer.errors),
                errors=SerializerErrorHandler.format_errors(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        if session_key:
            merge_guest_cart_to_user(session_key, user)
        
        response_data = {
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }
        
        return ResponseHandler.success_response(
            message="Authentication successful.",
            data=response_data,
            status_code=status.HTTP_200_OK
        )
    



class CustomTokenRefreshAPIView(TokenRefreshView):
    """
    Endpoint to send a valid refresh token in exchange for a brand new short-lived access token.
    """
    @extend_schema(auth=[])
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return ResponseHandler.success_response(
                message="Token refreshed successfully.",
                data=response.data,
                status_code=status.HTTP_200_OK
            )
        except (TokenError, InvalidToken) as e:
            return ResponseHandler.error_response(
                message="Invalid or expired refresh token.",
                errors={"refresh": [str(e)]},
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class LogoutAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        # Pass data to the serializer to handle validation cleanly
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseHandler.error_response(
                message="Refresh token is required to log out.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return ResponseHandler.success_response(
                message="Logout successful.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except (TokenError, InvalidToken):
            return ResponseHandler.error_response(
                message="Token is already invalid, expired, or blacklisted.",
                errors={"refresh": ["Invalid token structure."]},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
class ProfileAPIView(GenericAPIView):
    """
    Endpoint to retrieve the profile details of the currently authenticated session user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        # request.user is automatically populated by SimpleJWT using the incoming access token
        serializer = self.get_serializer(request.user)
        
        return ResponseHandler.success_response(
            message="User profile retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )