import logging
from rest_framework.permissions import IsAdminUser
from apps.core.views.base_view import BaseAPIViewSet
from apps.core.utils.cache_manager import CacheManager

from apps.products.models import ProductVariant
from apps.products.serializers.product_serializer import ProductVariantSerializer

logger = logging.getLogger(__name__)

class ProductVariantViewSet(BaseAPIViewSet):
    """
    Administrative controller for managing individual item SKUs,
    pricing frameworks, and real-time stock balances.
    """
    queryset = ProductVariant.objects.filter(is_active=True, is_deleted=False).select_related("product")
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.delete(user=self.request.user)