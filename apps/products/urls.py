from django.urls import path, include
from rest_framework.routers import SimpleRouter
from apps.products.views import CategoryViewSet, ProductViewSet, ProductVariantViewSet, InventoryLogViewSet

app_name = "products"

# Initialize the router engine
router = SimpleRouter()

# Register the viewsets to populate the routing matrix
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'items', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='variant')
router.register(r'inventory-logs', InventoryLogViewSet, basename='inventory-log')

urlpatterns = [
    path('', include(router.urls)),
]