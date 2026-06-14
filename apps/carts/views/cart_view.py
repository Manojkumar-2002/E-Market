from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from apps.core.utils.response_handler import ResponseHandler
from apps.core.utils.serializer_handler import SerializerErrorHandler
from apps.carts.models import Cart, CartItem
from apps.carts.serializers import CartSerializer, CartItemSerializer, AddToCartSerializer


class BaseCartAPIView(APIView):
    """Abstract helper base class to centralize session handling and cart isolation logic."""
    permission_classes = [AllowAny]

    def _get_or_create_cart(self, request) -> Cart:
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            return cart
        
        if not request.session.session_key:
            request.session.create()
            
        cart, _ = Cart.objects.get_or_create(
            user=None, 
            session_key=request.session.session_key
        )
        return cart


class CartAPIView(BaseCartAPIView):
    """
    Handles operations targeting the primary cart instance root container.
    Endpoints: GET /api/v1/carts/, POST /api/v1/carts/
    """
    serializer_class = CartSerializer

    @extend_schema(responses={200: CartSerializer})
    def get(self, request):
        """Retrieve the current active shopping basket with optimal relational joins."""
        cart = self._get_or_create_cart(request)
        
        # Optimize queries by pre-fetching nested variants and parent products
        cart_items = CartItem.objects.filter(cart=cart).select_related("variant__product")
        cart.items.all = lambda: cart_items 
        
        serializer = self.serializer_class(cart)
        return ResponseHandler.success_response(
            message="Cart retrieved successfully.",
            data=serializer.data
        )
    
    @extend_schema(
        request=AddToCartSerializer,
        responses={21: CartItemSerializer}
    )
    def post(self, request):
        """Add a product variant line item into the basket or increments its current volume."""
        cart = self._get_or_create_cart(request)
        serializer = AddToCartSerializer(data=request.data, context={"request": request})
        
        if not serializer.is_valid():
            return ResponseHandler.error_response(
                message=SerializerErrorHandler.get_first_error_message(serializer.errors),
                errors=SerializerErrorHandler.format_errors(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        variant = serializer.validated_data["variant"]
        requested_quantity = serializer.validated_data["quantity"]

        # Fetch or initialize the specific item row atomically
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={"quantity": requested_quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + requested_quantity
            if new_quantity > variant.stock_quantity:
                return ResponseHandler.error_response(
                    message=f"Cannot add. Combined cart total ({new_quantity}) exceeds available stock ({variant.stock_quantity}).",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()

        return ResponseHandler.success_response(
            message="Item added to cart successfully.",
            data=CartItemSerializer(cart_item).data,
            status_code=status.HTTP_201_CREATED
        )


class CartItemDetailAPIView(BaseCartAPIView):
    """
    Handles operations targeting unique individual line items inside the active cart.
    Endpoints: PATCH /api/v1/carts/items/<item_id>/, DELETE /api/v1/carts/items/<item_id>/
    """
    serializer_class = CartItemSerializer

    @extend_schema(
        request=CartItemSerializer,
        responses={200: CartItemSerializer}
    )
    def patch(self, request, item_id):
        """Perform dynamic incremental volume adjustments on an active cart item."""
        cart = self._get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        serializer = CartItemSerializer(cart_item, data=request.data, partial=True)
        if not serializer.is_valid():
            return ResponseHandler.error_response(
                message=SerializerErrorHandler.get_first_error_message(serializer.errors),
                errors=SerializerErrorHandler.format_errors(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        serializer.save()
        return ResponseHandler.success_response(
            message="Cart item updated successfully.",
            data=serializer.data
        )
    
    @extend_schema(responses={200: None})
    def delete(self, request, item_id):
        """Purges a variant row completely from the user's active shopping basket container."""
        cart = self._get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        # 👑 THE FIX: Purge the row permanently from physical disk storage
        cart_item.hard_delete()
        
        return ResponseHandler.success_response(
            message="Item permanently removed from cart successfully.",
            status_code=status.HTTP_200_OK
        )