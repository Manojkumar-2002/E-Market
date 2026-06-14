from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.users.views import (
    RegisterAPIView, 
    LoginAPIView, 
    CustomTokenRefreshAPIView, 
    LogoutAPIView,
    ProfileAPIView,
    AddressViewSet
)

app_name = "users"


# 1. Initialize the router and register the endpoint vector
router = SimpleRouter()
router.register(r"addresses", AddressViewSet, basename="address")



urlpatterns = [
    # Core Authentication Routes
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    
    # Token Management Routes
    path("token/refresh/", CustomTokenRefreshAPIView.as_view(), name="token_refresh"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path("", include(router.urls)),
]