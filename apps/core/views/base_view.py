from rest_framework import viewsets, status
from ..utils.response_handler import ResponseHandler
from ..utils.serializer_handler import SerializerErrorHandler


class BaseAPIViewSet(viewsets.ModelViewSet):
    """
    Universal Base: Only handles HTTP responses and error formatting.
    Override perform_create/perform_update/perform_destroy in subclasses for custom logic.
    """

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
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination_data = {
                'count': self.paginator.page.paginator.count,
                'page': self.paginator.page.number,
                'total_pages': self.paginator.page.paginator.num_pages,
            }
            return ResponseHandler.success_response(
                "Fetched successfully",
                data=serializer.data,
                pagination=pagination_data
            )

        serializer = self.get_serializer(queryset, many=True)
        return ResponseHandler.success_response("Fetched successfully", data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponseHandler.success_response("Fetched successfully", data=serializer.data)