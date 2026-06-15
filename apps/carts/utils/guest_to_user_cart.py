from ..models import Cart, CartItem
from django.db import transaction


def merge_guest_cart_to_user(session_key, user):
    try:
        guest_cart = Cart.objects.get(user=None, session_key=session_key)
    except Cart.DoesNotExist:
        return

    try:
        user_cart = Cart.objects.get(user=user)
        # User already has a cart — merge items carefully
        with transaction.atomic():
            for guest_item in guest_cart.items.all():
                user_item, created = CartItem.objects.get_or_create(
                    cart=user_cart,
                    variant=guest_item.variant,
                    defaults={"quantity": guest_item.quantity}
                )
                if not created:
                    # Same variant exists in user cart — combine quantities
                    user_item.quantity += guest_item.quantity
                    user_item.save()

            guest_cart.hard_delete()

    except Cart.DoesNotExist:
        # User has no cart — just claim the guest cart
        guest_cart.user = user
        guest_cart.session_key = None
        guest_cart.save()