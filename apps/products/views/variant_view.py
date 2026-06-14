import logging
from rest_framework.permissions import IsAdminUser, AllowAny
from apps.core.views.base_view import BaseAPIViewSet
from apps.core.utils.cache_manager import CacheManager

from apps.products.models import ProductVariant
from apps.products.serializers.product_serializer import ProductVariantSerializer

logger = logging.getLogger(__name__)



class ProductVariantViewSet(BaseAPIViewSet):
    """
    Administrative controller for managing individual item SKUs,
    pricing frameworks, and real-time stock balances.
    Allows public access for reading (listing/retrieving) variants.
    """
    queryset = ProductVariant.objects.filter(is_active=True, is_deleted=False).select_related("product")
    serializer_class = ProductVariantSerializer

    def get_permissions(self):
        """
        Dynamically splits permission scopes:
        - GET (list/retrieve) requests are open to everyone.
        - POST, PUT, PATCH, DELETE requests strictly require admin credentials.
        """
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.delete(user=self.request.user)