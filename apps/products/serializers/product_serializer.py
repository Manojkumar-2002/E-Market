from rest_framework import serializers
from apps.products.models import Product, Category, ProductVariant
from django.contrib.auth import get_user_model
from .variant_serializer import ProductVariantSerializer

User = get_user_model()

class UserAuditSerializer(serializers.ModelSerializer):
    """Minimal user footprint for audit tracking readability."""
    class Meta:
        model = User
        fields = ["id","email"]



class CategorySerializer(serializers.ModelSerializer):
    
    # 👑 Overriding the name field to inject explicit, custom error messages
    name = serializers.CharField(
        max_length=255,
        error_messages={
            "blank": "Category name cannot be empty.",
            "max_length": "Category name cannot exceed 255 characters.",
            "required": "The category name field is strictly required."
        }
    )

    class Meta:
        model = Category
        # Assuming your Category model has standard soft-delete/active states
        fields = ["id", "name", "slug", "is_active"] 
        read_only_fields = ["slug"] # Usually auto-generated from the name in the save() method

    def validate(self, attrs):
        """
        Object-level validation handling text sanitization and duplicate checking
        safely tailored for soft-deleted elements.
        """
        # 1. Clean up spacing and block whitespace-only strings
        if "name" in attrs:
            attrs["name"] = attrs["name"].strip()
            if not attrs["name"]:
                raise serializers.ValidationError({
                    "name": "Category name cannot consist of blank spaces."
                })

        # 2. Case-Insensitive Duplicate Check (Ignore soft-deleted categories)
        name = attrs.get("name")
        
        category_pool = Category.objects.filter(
            name__iexact=name,
            is_deleted=False
        )
        
        # If updating an existing category, exclude it from the duplicate search pool
        if self.instance:
            category_pool = category_pool.exclude(id=self.instance.id)

        if category_pool.exists():
            raise serializers.ValidationError({
                "name": f"A category named '{name}' already exists in the catalog."
            })

        return attrs




# 2. 🚀 LIGHTWEIGHT LISTING: Stays clean, simple, and perfectly cache-friendly
class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", 
            "category", 
            "name", 
            "is_active", 
            "created_at"
        ]


# 3. 💎 COMPLETE DETAIL: Deep point-lookup sheet incorporating real-time variant arrays
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    
    # 👑 THE INTEGRATION: Pulls all child variants linked via related_name="variants"
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    created_by = UserAuditSerializer(read_only=True)
    updated_by = UserAuditSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", 
            "category", 
            "name", 
            "description", 
            "is_active", 
            "variants",
            "created_at", 
            "updated_at",
            "is_deleted",
            "deleted_at",
            "created_by",
            "updated_by"
        ]



class ProductWriteSerializer(serializers.ModelSerializer):
    
    name = serializers.CharField(
        max_length=255,
        error_messages={
            "blank": "Product name cannot be empty.",
            "max_length": "Product name cannot exceed 255 characters.",
            "required": "The name field is strictly required."
        }
    )
    
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_deleted=False),
        error_messages={
            "does_not_exist": "The selected category does not exist in our catalog.",
            "incorrect_type": "Incorrect type. Expected a category primary key ID.",
            "null": "Product must be assigned to a valid category.",
            "required": "The category ID field is strictly required."
        }
    )

    class Meta:
        model = Product
        fields = ["id", "category", "name", "description", "is_active"]

    def validate_category(self, value):
        """
        Business Rule: Ensure the assigned category is active.
        """
        if hasattr(value, 'is_active') and not value.is_active:
            raise serializers.ValidationError(
                "Cannot assign product to an inactive category."
            )
        return value

    def validate(self, attrs):
        """
        Object-level validation handling text sanitization and localized uniqueness.
        """
        # 1. Clean up spacing
        if "name" in attrs:
            attrs["name"] = attrs["name"].strip()
            if not attrs["name"]:
                raise serializers.ValidationError({
                    "name": "Product name cannot consist of blank spaces."
                })

        # 2. Localized Uniqueness Check (Only scope to active, non-deleted items in the SAME category)
        name = attrs.get("name")
        category = attrs.get("category")
        
        # If updating an existing item, exclude it from the duplicate search pool
        product_pool = Product.objects.filter(
            category=category,
            name__iexact=name,  # Case-insensitive check (e.g., 'Mouse' matches 'mouse')
            is_deleted=False
        )
        
        if self.instance:
            product_pool = product_pool.exclude(id=self.instance.id)

        if product_pool.exists():
            raise serializers.ValidationError({
                "name": f"A product named '{name}' already exists inside this specific category."
            })

        return attrs

    def to_representation(self, instance):
        return ProductDetailSerializer(instance, context=self.context).data