from rest_framework import viewsets, status
from ..utils.response_handler import ResponseHandler
from ..utils.serializer_handler import SerializerErrorHandler
from ..pagination import CustomPageNumberPagination


class BaseAPIViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPageNumberPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseHandler.error_response(
                message=SerializerErrorHandler.get_first_error_message(serializer.errors),
                errors=SerializerErrorHandler.format_errors(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
        return ResponseHandler.success_response(
            "Created successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if not serializer.is_valid():
            return ResponseHandler.error_response(
                message=SerializerErrorHandler.get_first_error_message(serializer.errors),
                errors=SerializerErrorHandler.format_errors(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        self.perform_update(serializer)
        return ResponseHandler.success_response("Updated successfully", data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return ResponseHandler.success_response(message="Deleted successfully")
    
    def list(self, request, *args, **kwargs):
        """
        Paginator-agnostic list view. Handles both Cursor and PageNumber
        structures dynamically using dictionary envelopes.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            
            # Delegate metadata payload creation straight to the custom paginator
            response_envelope = self.paginator.get_paginated_response(serializer.data, as_dict=True)
            
            return ResponseHandler.success_response(
                message="Fetched successfully",
                data=response_envelope["data"],
                pagination=response_envelope["pagination"]
            )

        # 👑 THE FIX: Cleanly serialize and return the unpaginated fallback envelope
        serializer = self.get_serializer(queryset, many=True)
        return ResponseHandler.success_response(
            message="Fetched successfully",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponseHandler.success_response("Fetched successfully", data=serializer.data)