from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from ..utils.response_handler import ResponseHandler
from ..utils.serializer_handler import SerializerErrorHandler

def custom_exception_handler(exc, context):
    # 1. Call DRF's default exception handler first to get the standard response
    response = exception_handler(exc, context)

    # 2. If response is None, it means it's an unhandled exception (middleware will catch it)
    if response is None:
        return None

    # 3. Determine the message based on the exception type
    if isinstance(exc, ValidationError):
        message = SerializerErrorHandler.get_first_error_message(response.data)
        errors = SerializerErrorHandler.format_errors(response.data)
    elif isinstance(exc, NotAuthenticated):
        message = "Authentication credentials were not provided."
        errors = None
    elif isinstance(exc, AuthenticationFailed):
        message = "Invalid authentication credentials."
        errors = None
    elif isinstance(exc, PermissionDenied):
        message = "You do not have permission to perform this action."
        errors = None
    elif isinstance(exc, Throttled):
        message = f"Request was throttled. Try again in {exc.wait} seconds."
        errors = None
    else:
        # Fallback for other DRF exceptions
        message = _extract_message(response.data)
        errors = None

    # 4. Return your standardized ResponseHandler format
    return ResponseHandler.error_response(
        message=message,
        errors=errors,
        status_code=response.status_code
    )

def _extract_message(data):
    """Utility to flatten DRF's nested error dictionary into a single string."""
    if isinstance(data, dict):
        messages = []
        for key, value in data.items():
            if key == "non_field_errors":
                messages.extend(value if isinstance(value, list) else [value])
            else:
                # Handle nested dicts or lists
                error_msg = value[0] if isinstance(value, list) else value
                messages.append(f"{key}: {error_msg}")
        return " | ".join(str(m) for m in messages)
    
    if isinstance(data, list):
        return " | ".join(str(i) for i in data)
    
    return str(data)