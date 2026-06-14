from celery import shared_task
from django.db import transaction, OperationalError  # 👑 Import Django database exceptions
from django.db.models import F
import logging

logger = logging.getLogger(__name__)

# Configure autoretry specifically for database connection/locking operational failures
@shared_task(
    name="apps.orders.tasks.inspect_order_stock_ttl",
    bind=True,  # 👑 Gives us access to 'self' so we can call manual retries if needed
    autoretry_for=(OperationalError, ConnectionError),  # 👑 Catch these specific infra errors automatically
    retry_backoff=True,  # 🚀 Exponential backoff: waits 1s, then 2s, 4s, 8s...
    retry_kwargs={'max_retries': 5},  # Give up and drop the task after 5 attempts
    default_retry_delay=10  # Initial wait duration in seconds
)
def inspect_order_stock_ttl(self, order_id):  # 👑 Added 'self' as the first parameter
    from apps.orders.models import Order, OrderStatus
    from apps.products.models import ProductVariant, InventoryLog

    logger.info(f"⚡ Celery running structural audit logic for Order ID: {order_id}")

    try:
        # Keep object verification outside the atomic block to manage basic existence
        if not Order.objects.filter(id=order_id).exists():
            logger.error(f"❌ Critical: Order {order_id} missing from system tables.")
            return
    except (OperationalError, ConnectionError) as exc:
        # If the DB is completely down right at the start, log it and trigger a retry
        logger.warning(f"📡 Database connection error during pre-check. Retrying task... Error: {exc}")
        raise self.retry(exc=exc)

    with transaction.atomic():
        try:
            # Row-level lock
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return

        # ❌ CASE A: Checkout abandoned or payment session expired/timed out
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            order.save()

            for item in order.items.select_related('variant'):
                if item.variant:
                    variant = ProductVariant.objects.select_for_update().get(id=item.variant_id)
                    variant.stock_quantity = F("stock_quantity") + item.quantity
                    variant.save()
            logger.info(f"🔄 Stock values safely restored for Order {order_id}.")

        # ✅ CASE B: Successful checkout payment received
        elif order.status in [OrderStatus.PROCESSING, OrderStatus.COMPLETED]:
            log_exists = InventoryLog.objects.filter(
                action="CUSTOMER_ORDER",
                notes__contains=f"Order ID: {order.id}"
            ).exists()

            if log_exists:
                logger.info(f"🔄 Idempotency Guard hit: Logs already recorded for Order {order_id}.")
                return

            for item in order.items.select_related('variant'):
                if item.variant:
                    InventoryLog.objects.create(
                        variant=item.variant,
                        quantity_changed=-item.quantity,
                        action="CUSTOMER_ORDER",
                        notes=f"Successful sale ledger confirmation for Order ID: {order.id}",
                        created_by=order.user,
                        updated_by=order.user
                    )
            logger.info(f"✅ Compliance ledger updated successfully for Order {order_id}.")
        
        else:
            logger.info(f"ℹ️ Idempotency Guard hit: Order {order_id} is in status '{order.status}'.")