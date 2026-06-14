from rest_framework import serializers
from apps.products.models import InventoryLog

class InventoryLogSerializer(serializers.ModelSerializer):
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    updated_by_email = serializers.EmailField(source="updated_by.email", read_only=True)
    quantity_changed = serializers.IntegerField(
        min_value=-1000000, # Adjust based on your business constraints
        max_value=1000000,  # Stops out-of-range numbers cleanly at the serializer layer
        error_messages={
            "max_value": "Value is too large. Warehouse adjustments cannot exceed 1,000,000 items per log entry.",
            "min_value": "Value is too low. Outbound adjustments cannot exceed -1,000,000 items per log entry."
        }
    )

    class Meta:
        model = InventoryLog
        fields = [
            "id",
            "variant",
            "variant_sku",
            "quantity_changed",
            "action",
            "notes",
            "reference_order_id",
            "audit_metadata",
            "created_at",
            "updated_at",
            "created_by_email",
            "updated_by_email"
        ]
        read_only_fields = ["id", "reference_order_id", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 👑 YOUR OPTIMIZATION: If updating, make variant strictly read-only
        if self.instance is not None:
            self.fields['variant'].read_only = True