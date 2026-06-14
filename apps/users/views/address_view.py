from rest_framework.permissions import IsAuthenticated
from apps.core.views import BaseAPIViewSet
from apps.users.models import Address
from apps.users.serializers.address_serializer import AddressSerializer

class AddressViewSet(BaseAPIViewSet):
    """
    ViewSet for managing user-specific delivery addresses.
    All actions are automatically scoped down to the active logged-in user.
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Enforce strict data isolation: A user can ONLY query or alter 
        their own saved address vectors. Skips soft-deleted items if applicable.
        """
        user = self.request.user
        # Base query filtered exclusively by user context
        queryset = Address.objects.filter(user=user)
        
        # If your AuditModel has an 'is_deleted' flag, filter it out here:
        if hasattr(Address, 'is_deleted'):
            queryset = queryset.filter(is_deleted=False)
            
        return queryset

    def perform_create(self, serializer):
        """
        Intercept the save cycle to bind the address container directly 
        to the authenticated user making the HTTP request.
        """
        serializer.save(user=self.request.user)