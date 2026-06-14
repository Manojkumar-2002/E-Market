from decimal import Decimal
from rest_framework import serializers
from apps.products.models import Product, ProductVariant



class ProductVariantSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_deleted=False)
    )
    
    price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal('0.00'),
        allow_null=False,         
        default=Decimal('0.00')
    )
    
    stock_quantity = serializers.IntegerField(
        min_value=0,
        allow_null=False,
        default=0
    )

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product",
            "sku",
            "price",
            "stock_quantity",
            "size",
            "color",
            "is_active"
        ]

    def create(self, validated_data):
        """Handles POST: Initializes the variant with whatever stock is passed."""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Handles PUT/PATCH: Explicitly drops stock_quantity so it cannot be altered."""
        # 👑 THE CLEAN POP: If it's in the incoming payload, vaporize it right here
        validated_data.pop('stock_quantity', None)

        return super().update(instance, validated_data)
    