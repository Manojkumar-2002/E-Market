# config/settings/components/jwt_auth.py
from datetime import timedelta

def get_jwt_auth_config(env):
    """
    Encapsulates Django REST Framework Security, Throttling, and SimpleJWT
    token lifetimes. Reads expiration overrides from environment variables if present.
    """
    return {
        "REST_FRAMEWORK": {
            'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'rest_framework_simplejwt.authentication.JWTAuthentication',
            ),
            'DEFAULT_PERMISSION_CLASSES': (
                'rest_framework.permissions.IsAuthenticated',
            ),
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
                "rest_framework.throttling.UserRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                # Fallback defaults if not set in .env
                "anon": env.str("THROTTLE_RATE_ANON", default="20/minute"),
                "user": env.str("THROTTLE_RATE_USER", default="100/minute"),
            },
            "EXCEPTION_HANDLER": "apps.core.exceptions.drf_exception_handler.custom_exception_handler",
        },
        
        "SIMPLE_JWT": {
            # Allows you to easily change token expirations in production via .env
            'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int("JWT_ACCESS_LIFETIME_MINUTES", default=30)),
            'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int("JWT_REFRESH_LIFETIME_DAYS", default=1)),
            'ROTATE_REFRESH_TOKENS': True,
            'AUTH_HEADER_TYPES': ('Bearer',),
        },
        
        "SPECTACULAR_SETTINGS": {
            'TITLE': 'E-Market API Ecosystem',
            'DESCRIPTION': 'Core backend services for registration, authentication, and marketplace logistics.',
            'VERSION': '1.0.0',
            'SERVE_INCLUDE_SCHEMA': False,
            'COMPONENT_SPLIT_REQUEST': True,
            'POSTMAN_SPEC_COMPAT': True,
        }
    }