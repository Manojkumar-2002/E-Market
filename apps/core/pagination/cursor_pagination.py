from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

class CustomCursorPagination(CursorPagination):
    """
    High-performance cursor pagination backend.
    Uses constant $O(1)$ index traversal instead of slow database OFFSETS.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    # 👑 THE FIX: Order by timestamp primarily, fall back to ID/UUID as a unique tie-breaker
    ordering = ('-created_at', '-id')  

    def get_paginated_response(self, data, as_dict=False):
        response_data = {
            'pagination': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page_size': self.get_page_size(self.request),
            },
            'data': data
        }
        
        if as_dict:
            return response_data
            
        return Response(response_data)