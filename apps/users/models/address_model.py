# apps/accounts/models.py (or apps/users/models.py)
from django.db import models
from django.conf import settings
from apps.core.models import AuditModel 

class Address(AuditModel):
    ADDRESS_TYPES = (
        ("HOME", "Home"),
        ("OFFICE", "Office"),
        ("OTHER", "Other"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default="HOME")
    is_default = models.BooleanField(default=False)
    
    # Core Address Data
    full_name = models.CharField(max_length=255, help_text="Recipient name")
    phone_number = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="India")

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "address_type"],
                name="unique_user_address_type"
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.address_type} ({self.city})"

    def save(self, *args, **kwargs):
        # Business Rule: If this address is set to default, ensure all other 
        # addresses for this user are toggled to False automatically.
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)