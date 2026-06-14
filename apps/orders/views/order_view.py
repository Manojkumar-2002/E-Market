from django.db import transaction
from django.db.models import F
from rest_framework.views import APIView
from rest_framework import status, permissions, serializers

from apps.orders.models import Order, OrderItem
from apps.orders.serializers import CheckoutRequestSerializer
from apps.products.models import ProductVariant
from apps.orders.tasks import inspect_order_stock_ttl
from apps.carts.models import Cart, CartItem 
from apps.users.models import Address
from apps.users.serializers import AddressSerializer

from apps.core.utils.response_handler import ResponseHandler  
from apps.core.utils.serializer_handler import SerializerErrorHandler


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        🚀 RECONCILIATION RESERVATION ENGINE:
        Processes raw user carts, drops variant counts to execute holds, 
        clears out the user's active shopping cart items completely, and 
        schedules the 5-minute delayed structural timeout validation check.
        """
        # Pass request context so validators can execute user boundary context isolation checks
        serializer = CheckoutRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return ResponseHandler.error_response(
                message=SerializerErrorHandler.get_first_error_message(serializer.errors),
                errors=SerializerErrorHandler.format_errors(serializer.errors),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        cart_items = validated_data['items']

        try:
            # 1. Fetch address and build the snapshot cleanly outside the transaction block
            address_record = validated_data['address']


            address_snapshot = AddressSerializer(address_record, context={'request': request}).data

            # 2. Open our isolated transactional pipeline
            with transaction.atomic():
                # Initialize pending base invoice master
                order = Order.objects.create(
                    user=request.user,
                    shipping_address_snapshot=address_snapshot, # ❄️ Purely isolated JSON data
                    total_amount=0,
                    created_by=request.user,
                    updated_by=request.user
                )
                
                calculated_total = 0
                variant_ids_to_clear = []

                # 3. Iterate and verify items using absolute pessimistic database row locking
                for item in cart_items:
                    variant_id = item['variant_id']
                    quantity = item['quantity']
                    variant_ids_to_clear.append(variant_id)

                    # 🔒 ROW-LEVEL LOCK: Stops parallel over-selling checks dead in their tracks
                    variant = ProductVariant.objects.select_for_update().get(id=variant_id, is_deleted=False)

                    # Verify locked row value against request values
                    if variant.stock_quantity < quantity:
                        raise serializers.ValidationError(
                            f"Reservation failed. SKU '{variant.sku}' does not have enough stock remaining."
                        )

                    # Cache price data before applying F expressions
                    item_price = variant.price

                    # Atomically deduct the allocation count to run the consumer hold
                    variant.stock_quantity = F("stock_quantity") - quantity
                    variant.save()

                    # 4. Compile structural historical snapshots inside the OrderItem rows
                    OrderItem.objects.create(
                        order=order,
                        variant=variant,
                        quantity=quantity,
                        price_at_purchase=item_price,
                        sku_snapshot=variant.sku,
                        metadata_snapshot={
                            "size": getattr(variant, 'size', None),
                            "color": getattr(variant, 'color', None)
                        },
                        created_by=request.user,
                        updated_by=request.user
                    )
                    
                    calculated_total += item_price * quantity

                # Finalize master ledger financial totals
                order.total_amount = calculated_total
                order.save()

                # 5. PERMANENTLY PURGE CART ITEMS AT THE TRANSACTION HORIZON
                CartItem.objects.filter(
                    cart__user=request.user, 
                    variant_id__in=variant_ids_to_clear
                ).hard_delete()

                # 👑 THE DELAYED TRIGGER: Routed directly to our fast-lane checkout worker queue
                transaction.on_commit(lambda: inspect_order_stock_ttl.apply_async(
                    args=[str(order.id)], 
                    countdown=600  # Exactly 5 minutes delay (300 seconds)
                ))

            # 👑 SUCCESS PATH: Standardized via ResponseHandler
            return ResponseHandler.success_response(
                message="Stock successfully reserved and cart cleared. Please complete payment within 5 minutes.",
                data={
                    "order_id": order.id,
                    "total_amount": str(calculated_total)
                },
                status_code=status.HTTP_201_CREATED
            )

        except ProductVariant.DoesNotExist:
            return ResponseHandler.error_response(
                message="An item in your cart no longer exists.",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except serializers.ValidationError as e:
            
            return ResponseHandler.error_response(
                message=SerializerErrorHandler.get_first_error_message(e.detail),
                errors=SerializerErrorHandler.format_errors(e.detail),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import permissions, status
from django.db.models import Prefetch

from apps.orders.models import Order, OrderItem
from apps.orders.serializers import OrderSerializer
from apps.core.utils.response_handler import ResponseHandler


class OrderViewSet(ReadOnlyModelViewSet):
    """
    🛡️ MULTI-TENANT ORDER LEDGER GATEWAY:
    Automates read-only access boundaries for order endpoints.
    - Admins/Staff: Access global records.
    - Regular Customers: Automatically sandboxed to their own rows.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        """
        👑 DYNAMIC DATA ISOLATION ENGINE:
        Evaluates boundary context dynamically before reading rows.
        """
        user = self.request.user

        if user.is_staff or user.is_superuser:
            base_queryset = Order.objects.all()
        else:
            base_queryset = Order.objects.filter(user=user)

        # ⚡ OPTIMIZATION ENGINE: Database prefetching to neutralize N+1 query overhead
        return base_queryset.select_related('user').prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('variant__product')
            )
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """Standardizes list payload responses using ResponseHandler."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return ResponseHandler.success_response(
            message="Orders retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        """Standardizes detail payload responses using ResponseHandler."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponseHandler.success_response(
            message="Order details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )