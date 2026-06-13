from django.urls import path
from apps.users.views import (
    RegisterAPIView, 
    LoginAPIView, 
    CustomTokenRefreshAPIView, 
    LogoutAPIView,
    ProfileAPIView
)

# The app_name sets a namespace so you can reverse look up these URLs (e.g., 'users:login')
app_name = "users"

urlpatterns = [
    # Core Authentication Routes
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    
    # Token Management Routes
    path("token/refresh/", CustomTokenRefreshAPIView.as_view(), name="token_refresh"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
]