from rest_framework import serializers
from decimal import Decimal
from apps.carts.models import Cart, CartItem
from apps.products.models import ProductVariant


class CartItemVariantSerializer(serializers.ModelSerializer):
    """Lean serializer to nest essential variant properties into the cart payload."""
    product_name = serializers.CharField(source="product.name", read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "product_name", "price", "size", "color", "stock_quantity"]


class CartItemSerializer(serializers.ModelSerializer):
    """
    USED FOR READS (GET) & PARTIAL UPDATES (PATCH).
    The variant_id is omitted here because a line item's variant is immutable once created.
    """
    variant = CartItemVariantSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "variant", "quantity", "line_total"]
        read_only_fields = ["id", "variant", "line_total"]

    def get_line_total(self, obj) -> str:
        """Dynamically computes line total: quantity * price."""
        return f"{(obj.quantity * obj.variant.price):.2f}"

    def validate(self, attrs):
        """Validates stock requirements purely based on the item's bound variant instance."""
        # This serializer is only validated during PATCH requests
        if self.instance:
            variant = self.instance.variant
            quantity = attrs.get("quantity", self.instance.quantity)

            if quantity > variant.stock_quantity:
                raise serializers.ValidationError({
                    "quantity": f"Only {variant.stock_quantity} units available in stock. Cannot fulfill request for {quantity} units."
                })
        return attrs


class AddToCartSerializer(serializers.Serializer):
    """
    USED EXCLUSIVELY FOR CREATION (POST).
    Explicitly requires variant_id from the product catalog page layout context.
    """
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(is_active=True, is_deleted=False),
        source="variant"
    )
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        """Verify warehouse stock inventory limits before allowing item addition."""
        variant = attrs["variant"]
        quantity = attrs.get("quantity", 1)

        if quantity > variant.stock_quantity:
            raise serializers.ValidationError({
                "quantity": f"Only {variant.stock_quantity} units available in stock. Cannot fulfill request for {quantity} units."
            })
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    cart_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ["id", "total_items_count", "cart_total", "items"]
        read_only_fields = ["id", "total_items_count", "cart_total", "items"]

    def get_cart_total(self, obj) -> str:
        """Sums up the line totals of all child items inside the basket container."""
        total = sum(item.quantity * item.variant.price for item in obj.items.all())
        return f"{total:.2f}"