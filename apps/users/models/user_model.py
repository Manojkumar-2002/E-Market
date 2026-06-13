from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.core.models import BaseModel


class UserManager(BaseUserManager):
    """
    Custom manager for Custom User model where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Strict email-authenticated Custom User model.
    Inherits UUID 'id', 'created_at', and 'updated_at' automatically from BaseModel,
    and permissions groups from PermissionsMixin.
    """
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Core administrative status flags required by Django
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Assign our custom manager logic to this model
    objects = UserManager()

    # Configure authentication behavior
    USERNAME_FIELD = "email"     # Field used as unique identifier for logging in
    REQUIRED_FIELDS = []         # Fields prompted for when running createsuperuser

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email