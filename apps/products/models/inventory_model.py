from django.db import models
from apps.core.models import AuditModel

class InventoryLog(AuditModel):
    """
    Tracks every single incoming or outgoing physical stock change 
    with absolute origin traceability. Inherits baseline tracking from AuditModel.
    """
    class ActionType(models.TextChoices):
        RESTOCK = "RESTOCK", "New Shipment Arrival"
        RETURNS = "RETURNS", "Customer Return Refund"
        CORRECTION = "CORRECTION", "Manual Audit Adjustment"
        ORDER_DEDUCTION = "ORDER_DEDUCTION", "Fulfillment Allocation"
        TIMEOUT_REFUND = "TIMEOUT_REFUND", "Checkout Session Expiration"

    variant = models.ForeignKey(
        "products.ProductVariant", 
        on_delete=models.CASCADE, 
        related_name="inventory_logs"
    )
    quantity_changed = models.IntegerField(help_text="Positive for incoming, negative for outgoing.")
    action = models.CharField(max_length=20, choices=ActionType.choices)
    notes = models.TextField(blank=True, null=True)
    
    # Traceability links
    reference_order_id = models.UUIDField(
        blank=True, 
        null=True, 
        help_text="The original purchase invoice ID if applicable."
    )
    audit_metadata = models.JSONField(
        blank=True, 
        null=True, 
        help_text="Stores event-specific context like return_slip_id or admin data."
    )

    class Meta:
        ordering = ["-created_at"]
        db_table = "market_inventory_logs"

    def __str__(self):
        return f"{self.action} ({self.quantity_changed}) -> {self.variant.sku}"