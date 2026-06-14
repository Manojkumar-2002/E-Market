from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser
from apps.core.views import BaseAPIViewSet
from apps.products.models import InventoryLog, ProductVariant
from apps.products.serializers import InventoryLogSerializer


class InventoryLogViewSet(BaseAPIViewSet):
    """
    🔒 ADMINISTRATIVE COMPLIANCE LEDGER:
    Manages audit records and automatically recalculates physical 
    ProductVariant stocks atomically using fixed row history references.
    """
    queryset = InventoryLog.objects.all().select_related("variant", "created_by", "updated_by")
    serializer_class = InventoryLogSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        """Handles POST: Creates a new entry and increments live inventory."""
        with transaction.atomic():
            log_instance = serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )

            # Row lock using the new instance data reference
            variant = ProductVariant.objects.select_for_update().get(id=log_instance.variant_id)

            if variant.stock_quantity + log_instance.quantity_changed < 0:
                raise serializers.ValidationError({
                    "quantity_changed": f"Operation rejected. Live stock cannot drop below zero."
                })

            variant.stock_quantity = F("stock_quantity") + log_instance.quantity_changed
            variant.save()

    def perform_update(self, serializer):
        """
        Handles PUT/PATCH: Pulls the invariant variant reference straight from the 
        existing row ledger memory, completely ignoring the request payload parameters.
        """
        with transaction.atomic():
            # 1. Fetch current immutable record state directly from disk
            old_log_state = self.get_object()
            old_quantity = old_log_state.quantity_changed
            
            # 👑 TAKE IT DIRECTLY FROM THE LOG ROW DATA REFERENCE:
            variant_id = old_log_state.variant_id 

            # 2. Save the text updates/quantities to disk memory safely
            updated_log_instance = serializer.save(updated_by=self.request.user)
            new_quantity = updated_log_instance.quantity_changed

            # 3. Calculate your variance delta adjustments
            stock_delta = new_quantity - old_quantity

            if stock_delta != 0:
                # 🔒 ROW-LEVEL LOCK: Use the structural database ID reference safely
                variant = ProductVariant.objects.select_for_update().get(id=variant_id)

                if variant.stock_quantity + stock_delta < 0:
                    raise serializers.ValidationError({
                        "quantity_changed": f"Correction rejected. Live stock cannot fall below zero. Current balance: {variant.stock_quantity}."
                    })

                # Securely apply delta mapping counter metrics
                variant.stock_quantity = F("stock_quantity") + stock_delta
                variant.save()