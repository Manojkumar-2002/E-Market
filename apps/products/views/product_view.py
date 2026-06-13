import logging

import hashlib
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.views.base_view import BaseAPIViewSet
from apps.core.utils.response_handler import ResponseHandler
from apps.core.utils.cache_manager import CacheManager
from apps.core.pagination import CustomCursorPagination

from apps.products.models import Category, Product
from apps.products.filters import ProductFilter
from apps.products.serializers.product_serializer import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer
)


logger = logging.getLogger(__name__)


class CategoryViewSet(BaseAPIViewSet):
    """
    Unified Category controller featuring transactional 
    soft-deletion and cascade restoration switches.
    """
    queryset = Category.objects.filter(is_active=True, is_deleted=False)
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
        CacheManager.bump_global_app_version()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
        CacheManager.bump_global_app_version()

    def perform_destroy(self, instance):
        # Pass user context to populate the audit trail during soft-deletion
        instance.delete(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="restore", permission_classes=[IsAdminUser])
    def restore_category(self, request, pk=None):
        """
        POST /api/v1/categories/<uuid>/restore/?include_products=true
        """
        try:
            # Bypass soft-delete filters using your custom manager lookup
            category = Category.objects.all_with_deleted().get(pk=pk)
        except Category.DoesNotExist:
            return ResponseHandler.error_response("Category not found.", status_code=404)

        if not category.is_deleted:
            return ResponseHandler.error_response("This category row is already active.")

        include_products = request.query_params.get("include_products", "true").lower() == "true"
        
        # Trigger your transactional model restoration pipeline
        category.restore(restore_products=include_products, user=request.user)

        return ResponseHandler.success_response(
            message=f"Category '{category.name}' and its relationships successfully restored."
        )





class ProductViewSet(BaseAPIViewSet):
    """
    High-throughput Product Controller utilizing schema-driven version caching 
    for lists, and strict real-time database tracking for detail sheets.
    """
    queryset = Product.objects.filter(is_active=True, is_deleted=False).select_related("category")
    pagination_class = CustomCursorPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        elif self.action in ["retrieve", "destroy"]:
            return ProductDetailSerializer
        return ProductWriteSerializer

    def list(self, request, *args, **kwargs):
        """
        Optimized listing view with deterministic query string parameter hashing
        to preserve page filters across isolated Redis cache keys.
        """
        category_id = request.query_params.get("category") or request.query_params.get("category_slug") or "global"

        # Extract and sort query params to ensure order-agnostic cache keys
        raw_params = request.query_params.copy()
        cursor_token = raw_params.get(self.pagination_class.cursor_query_param, "initial")
        
        sorted_params = sorted([(k, v) for k, v in raw_params.items()])
        filter_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        filter_hash = hashlib.md5(filter_string.encode("utf-8")).hexdigest()[:12]

        # Build clean cache key incorporating the specific query signature
        cache_key = CacheManager.build_registry_key(
            key_token="products",
            scope_id=category_id,
            details=f"cursor_{cursor_token}_filterset_{filter_hash}"
        )

        # 1. Safe Cache Evaluation
        cached_payload = CacheManager.get_cached_data(cache_key)
        if cached_payload is not None:
            return ResponseHandler.success_response(
                message="Fetched successfully (Cache Hit)",
                data=cached_payload["data"],
                pagination=cached_payload["pagination"]
            )

        # 2. Cache Miss -> Query Database and Paginate
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)
        
        serializer = self.get_serializer(page, many=True)
        response_envelope = self.paginator.get_paginated_response(serializer.data, as_dict=True)

        # 3. Cache state for 24 hours
        CacheManager.set_cached_data(cache_key, response_envelope, timeout=86400)

        return ResponseHandler.success_response(
            message="Fetched successfully (Database Read)",
            data=response_envelope["data"],
            pagination=response_envelope["pagination"]
        )

    def retrieve(self, request, *args, **kwargs):
        """
        No-cache retrieve view. 
        Forces a direct database read to guarantee real-time data 
        and accurate inventory metrics on checkout item landing pages.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return ResponseHandler.success_response(
            message="Fetched successfully (Real-time DB Read)", 
            data=serializer.data
        )


    def perform_create(self, serializer):
        product = serializer.save(created_by=self.request.user, updated_by=self.request.user)
        
        # 👑 THE FIX: Invalidate both the target category AND the global marketplace list
        CacheManager.bump_version(key_token="products", scope_id=product.category_id)
        CacheManager.bump_version(key_token="products", scope_id="global")

    def perform_update(self, serializer):
        # Handle cases where an admin switches a product from one category to another
        old_instance = self.get_object()
        old_category_id = old_instance.category_id
        
        product = serializer.save(updated_by=self.request.user)
        
        # 👑 THE FIX: Clear old category, new category, and the global catalog
        CacheManager.bump_version(key_token="products", scope_id=product.category_id)
        CacheManager.bump_version(key_token="products", scope_id="global")
        if old_category_id != product.category_id:
            CacheManager.bump_version(key_token="products", scope_id=old_category_id)

    def perform_destroy(self, instance):
        category_id = instance.category_id
        instance.delete(user=self.request.user)
        
        # 👑 THE FIX: Invalidate both on soft-deletion
        CacheManager.bump_version(key_token="products", scope_id=category_id)
        CacheManager.bump_version(key_token="products", scope_id="global")