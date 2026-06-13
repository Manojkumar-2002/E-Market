from django.db import models
from django.utils.text import slugify
from apps.core.models import AuditModel
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.postgres.indexes import GinIndex

class Category(AuditModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["-created_at", "-id"]),
            models.Index(fields=["is_deleted", "is_active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(AuditModel):
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        related_name="products"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["-created_at", "-id"]),
            models.Index(fields=["is_deleted", "is_active", "category_id"]),
            GinIndex(
                fields=["name"], 
                name="product_name_gin_trgm",
                opclasses=["gin_trgm_ops"] 
            ),
        ]

    def __str__(self):
        return self.name


class ProductVariant(AuditModel):
    product = models.ForeignKey(
        "Product", 
        on_delete=models.CASCADE, 
        related_name="variants"
    )
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    
    # 💰 THE FIX: Enforce non-negative values using MinValueValidator
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    
    size = models.CharField(max_length=50, blank=True, help_text="e.g., Size")
    color = models.CharField(max_length=50, blank=True, help_text="e.g., Color")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["is_deleted", "is_active", "product_id"]),
            models.Index(fields=["stock_quantity"]),
        ]

    def __str__(self):
        if self.size or self.color:
            return f"{self.product.name} - {self.color or 'N/A'} / {self.size or 'N/A'} ({self.sku})"
        return f"{self.product.name} (Default SKU: {self.sku})"