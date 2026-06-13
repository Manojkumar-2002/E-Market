from rest_framework import status
from rest_framework.response import Response


class ResponseHandler:
    """Utility class for handling API responses"""

    @staticmethod
    def success_response(message, data=None, pagination=None, status_code=status.HTTP_200_OK):
        """Standard success response format"""
        response_data = {
            'success': True,
            'message': message,
            'status_code': status_code,
            'data': data if data is not None else []
        }
        if pagination:
            response_data['pagination'] = pagination

        return Response(response_data, status=status_code)

    @staticmethod
    def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST, extra_data=None):
        """Standard error response format"""
        response_data = {
            'success': False,
            'message': message,
            'status_code': status_code
        }
        if errors:
            response_data['errors'] = errors

        if extra_data:
            response_data.update(extra_data)

        return Response(response_data, status=status_code)