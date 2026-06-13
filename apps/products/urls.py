from django.urls import path, include
from rest_framework.routers import SimpleRouter
from apps.products.views import CategoryViewSet, ProductViewSet, ProductVariantViewSet

app_name = "products"

# Initialize the router engine
router = SimpleRouter()

# Register the viewsets to populate the routing matrix
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'items', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='variant')

urlpatterns = [
    path('', include(router.urls)),
]