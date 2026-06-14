import re
from rest_framework import serializers
from apps.users.models import Address

class AddressSerializer(serializers.ModelSerializer):
 
    user = serializers.StringRelatedField(read_only=True)
    
    phone_number = serializers.CharField(
        max_length=20,
        error_messages={
            "blank": "Phone number cannot be empty.",
            "required": "Phone number is strictly required."
        }
    )

    class Meta:
        model = Address
        fields = [
            "id", "user", "address_type", "is_default", 
            "full_name", "phone_number", "address_line_1", 
            "address_line_2", "landmark", "city", "state", 
            "postal_code", "country", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

    def validate_phone_number(self, value):
        """
        Validates basic phone formatting rules (supports optional country code, spaces, dashes).
        """
        clean_value = value.strip()
        # Basic regex check allowing digits, leading plus sign, spaces, and hyphens
        if not re.match(r"^\+?[0-9\s\-]{10,20}$", clean_value):
            raise serializers.ValidationError("Enter a valid phone number format (e.g., +919876543210 or 9876543210).")
        return clean_value

    def validate(self, attrs):
        """
        Clean whitespace from all inbound text string components dynamically
        and enforce the unique-type constraint per user.
        """
        # 1. Clean whitespace and block empty-space strings
        text_fields = ["full_name", "address_line_1", "city", "state", "postal_code"]
        for field in text_fields:
            if field in attrs and isinstance(attrs[field], str):
                attrs[field] = attrs[field].strip()
                if not attrs[field]:
                    raise serializers.ValidationError({field: "This field cannot consist of blank spaces."})

        # 2. 👑 Enforce unique address_type constraint per user
        # Grab the authenticated user safely from the view context
        user = self.context['request'].user
        
        # If updating (PATCH), address_type might not be in attrs; fall back to the current record's type
        address_type = attrs.get("address_type") or (self.instance.address_type if self.instance else None)

        if address_type:
            # Query if this user already has an address using this specific category label
            existing_type_pool = Address.objects.filter(user=user, address_type=address_type)
            
            # If your model supports soft-deletion, filter out deleted vectors:
            if hasattr(Address, 'is_deleted'):
                existing_type_pool = existing_type_pool.filter(is_deleted=False)

            # If we are updating an existing entry, exclude it from the duplicate search pool
            if self.instance:
                existing_type_pool = existing_type_pool.exclude(id=self.instance.id)

            if existing_type_pool.exists():
                raise serializers.ValidationError({
                    "address_type": f"You already have a saved '{address_type}' address. Please edit that record or select a different type."
                })

        return attrs