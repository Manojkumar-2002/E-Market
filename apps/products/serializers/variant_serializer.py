# Inside apps/products/serializers/product_serializer.py
from ..models import Product, ProductVariant
from rest_framework import serializers
from decimal import Decimal


class ProductVariantSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_deleted=False),
        write_only=True
    )
    
    # 💰 THE FIX: Added fallback default while keeping strict null rejection
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