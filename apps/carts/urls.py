# apps/carts/urls.py
from django.urls import path
from apps.carts.views import CartAPIView, CartItemDetailAPIView

# Explicitly defining the app_name sets up a clean namespace framework for reverse lookups
app_name = "carts"

urlpatterns = [
    # 🛒 Primary Cart Endpoint (GET to fetch the basket, POST to add/increment items)
    path("", CartAPIView.as_view(), name="cart-root"),
    
    # ⚡ Targeted Item Modifier Endpoint (PATCH to change quantity, DELETE to remove item)
    path("items/<uuid:item_id>/", CartItemDetailAPIView.as_view(), name="cart-item-detail"),
]