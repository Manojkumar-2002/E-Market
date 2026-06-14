from rest_framework import serializers
from apps.products.models import ProductVariant
from apps.users.models import Address


class CheckoutItemSerializer(serializers.Serializer):
    # 👑 PURE FORMAT VALIDATION: Hits 0 databases
    variant_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(min_value=1, required=True)


class CheckoutRequestSerializer(serializers.Serializer):
    # 👑 Auto-validates existence and ownership, returning the Address object
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.none())
    
    items = serializers.ListField(
        child=CheckoutItemSerializer(),
        required=True,
        allow_empty=False
    )

    def __init__(self, *args, **kwargs):
        """
        🛡️ DYNAMIC QUERYSET FILTER:
        Injects the authenticated user's context directly into the 
        address validation field before the request runs.
        """
        super().__init__(*args, **kwargs)
        
        # Access the request context passed from the view
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            # Re-bind the address queryset to ONLY show this user's rows
            self.fields['address'].queryset = Address.objects.filter(user=request.user)

from rest_framework import serializers
from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    # Dynamically extract tracking metrics across foreign keys
    product_title = serializers.CharField(source='variant.product.title', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 
            'variant', 
            'product_title',
            'quantity', 
            'price_at_purchase', 
            'sku_snapshot', 
            'metadata_snapshot'
        ]


class OrderSerializer(serializers.ModelSerializer):
    # Maps directly to the pre-fetched structural database relationships
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 
            'customer_email',
            'shipping_address_snapshot', 
            'total_amount', 
            'status', 
            'created_at', 
            'items'
        ]