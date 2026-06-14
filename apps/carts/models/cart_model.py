from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.core.models import AuditModel
from apps.products.models import ProductVariant 

class Cart(AuditModel):
    """
    Parent container model representing a user's active shopping basket.
    Supports authenticated customers. For unauthenticated guest baskets, 
    falls back to an indexed session token string.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True,
        help_text="The authenticated account owner of this shopping basket."
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        db_index=True,
        help_text="Fallback tracker token to maintain persistent baskets for anonymous guest shoppers."
    )

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session_key"],
                name="unique_anonymous_guest_cart",
                condition=models.Q(user__isnull=True)
            )
        ]

    def __str__(self):
        if self.user:
            return f"Cart belonging to: {self.user.email}"
        return f"Anonymous Guest Cart: {self.session_key}"


    @property
    def total_items_count(self) -> int:
        """Calculates quantity totals completely within the database engine."""
        result = self.items.aggregate(total=Sum('quantity'))['total']
        return result or 0


class CartItem(AuditModel):
    """
    Child line-item model tracking individual specific ProductVariants 
    mapped inside an active parent shopping basket container.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        db_index=True
    )
    # 👑 THE VARIANT REFACTOR: We link directly to the specific variant SKU bought
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="cart_entries",
        db_index=True
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1, message="Item quantity cannot fall below 1 unit.")]
    )

    class Meta:
        ordering = ["-created_at"]
        # 👑 THE DATABASE GUARDRAIL: A single variant (e.g., Red/XL SKU) cannot be 
        # duplicated as separate rows inside the same basket container.
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="unique_cart_variant_line_item"
            )
        ]

    def __str__(self):
        return f"{self.quantity}x {self.variant.sku} inside Cart {self.cart_id}"
    
    