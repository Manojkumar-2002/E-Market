from django.urls import path, include
from apps.orders.views import CheckoutView, OrderViewSet
from rest_framework.routers import SimpleRouter

# 👑 Explicit namespace mapping for reverse URL lookups (e.g., 'orders:checkout')
app_name = "orders"

router = SimpleRouter()
router.register(r'orders', OrderViewSet, basename='order')


urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path('', include(router.urls)),
]


