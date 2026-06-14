from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.products.models import ProductVariant
# 👑 IMPORT YOUR CORE STRUCTURAL LAYER (Adjust the import path to match your folder structure)
from apps.core.models import AuditModel 


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Payment"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    FAILED = "FAILED", "Failed"


class Order(AuditModel):
  
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name="orders"
    )
    status = models.CharField(
        max_length=20, 
        choices=OrderStatus.choices, 
        default=OrderStatus.PENDING,
        db_index=True
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # ADDRESS SNAPSHOT: Dynamic structural JSON string data
    shipping_address_snapshot = models.JSONField(
        help_text="Immutable snapshot of the user shipping address properties at checkout millisecond."
    )

    class Meta(AuditModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} ({self.status})"


class OrderItem(AuditModel):
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="order_items"
    )
    
    # SKU PARAMETER SNAPSHOTS
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    sku_snapshot = models.CharField(max_length=100)
    metadata_snapshot = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Stores historical variant specifications like color and size sizing."
    )

    def __str__(self):
        return f"{self.quantity} x {self.sku_snapshot} (Order {self.order_id})"