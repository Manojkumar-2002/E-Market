import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """
    Custom QuerySet that automatically intercepts bulk delete actions
    and filters out soft-deleted records from standard queries.
    """
    def delete(self):
        # Converts bulk delete queries (e.g., QuerySet.delete()) into soft deletes
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        # Truncates or purges records permanently from the database disk
        return super().delete()


class SoftDeleteManager(models.Manager):
    """
    Manager that defaults to displaying only active (non-deleted) records.
    """
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        # Use this explicitly when an admin needs to see the absolute history
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    """
    Abstract base class model providing unique UUID primary keys
    and system-level timestamp metrics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditModel(BaseModel):
    """
    An abstract base class model providing robust audit tracking (who & when)
    and clean soft-delete capabilities for e-commerce tables.
    """
    # Audit Tracking Fields (Points dynamically to your custom User config)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_%(class)s_set",  # Avoids reverse relation collisions
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_%(class)s_set",
        null=True,
        blank=True
    )

    # Soft Delete Flags
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Attach the custom filtering manager
    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """Perform a soft delete by flipping flags instead of running an SQL DELETE."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Brings a soft-deleted database record back to life."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, *args, **kwargs):
        """Permanently purges the row from physical disk storage."""
        super().delete(*args, **kwargs)