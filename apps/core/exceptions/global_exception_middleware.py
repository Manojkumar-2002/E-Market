# apps/common/middleware.py
import logging
import traceback

from django.http import JsonResponse

logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exception:
            # This logic captures the crash
            logger.error(
                "Unhandled exception: %s\n%s",
                str(exception),
                traceback.format_exc(),
            )
            return JsonResponse(
                {
                    "error": True,
                    "status_code": 500,
                    "message": "An unexpected error occurred. Please try again later.",
                },
                status=500,
            )