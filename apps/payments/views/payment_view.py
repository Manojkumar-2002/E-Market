import json
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse

from apps.orders.models import Order, OrderStatus
from apps.payments.models import Transaction, TransactionStatus, PaymentGateway
from apps.payments.serializers import PaymentInitResponseSerializer
from apps.core.utils.payment_utils import client as razorpay_client
from apps.core.utils.response_handler import ResponseHandler

from apps.orders.tasks import generate_and_send_invoice_task


class InitializePaymentView(APIView):
    """
    💳 VIEW 1: PAY NOW INTENT GENERATOR
    Invoked when a user initializes payment for a locked order.
    Talks to the provider safely outside database transactions to prevent connection pool starvation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        # Step 1: Fast, isolated validation check to ensure order is payable
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return ResponseHandler.error_response(
                message="Requested order not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if order.status == OrderStatus.CANCELLED:
            return ResponseHandler.error_response(
                message="The payment window for this order has expired. Reserved stock has been released.",
                status_code=status.HTTP_410_GONE
            )
        if order.status == OrderStatus.COMPLETED:
            return ResponseHandler.error_response(
                message="This order has already been paid for successfully.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        # ✅ Also guard against re-initializing an already processing order
        if order.status == OrderStatus.PROCESSING:
            return ResponseHandler.error_response(
                message="A payment has already been initiated for this order.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Step 2: Safe external API call — DB is completely unlocked right now
        razorpay_payload = {
            "amount": int(order.total_amount * 100),
            "currency": "INR",
            "receipt": str(order.id),
            "payment_capture": 1
        }

        try:
            razorpay_order = razorpay_client.order.create(data=razorpay_payload)
        except Exception as e:
            return ResponseHandler.error_response(
                message=f"Payment gateway communication failed: {str(e)}",
                status_code=status.HTTP_502_BAD_GATEWAY
            )

        # Step 3: Atomic block — write gateway data and flip status to PROCESSING
        with transaction.atomic():
            try:
                # Re-fetch under a strict row lock to handle race conditions
                order = Order.objects.select_for_update().get(id=order_id)

                # Only proceed if still PENDING (guard against concurrent requests)
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.PROCESSING  # ✅ Mark as processing
                    order.transaction_id = razorpay_order['id']
                    order.save()

                    Transaction.objects.create(
                        order=order,
                        gateway=PaymentGateway.RAZORPAY,
                        gateway_order_id=razorpay_order['id'],
                        amount=order.total_amount,
                        status=TransactionStatus.PENDING,
                        raw_response_snapshot=razorpay_order,
                        created_by=request.user,
                        updated_by=request.user
                    )
            except Order.DoesNotExist:
                pass  # Fall through safely

        # Step 4: Build and return the response payload
        razorpay_key_id = settings.PAYMENTS.get("RAZORPAY", {}).get("KEY_ID", "")

        response_data = {
            "gateway_order_id": razorpay_order['id'],
            "amount": razorpay_order['amount'],
            "currency": razorpay_order['currency'],
            "key_id": razorpay_key_id,
            "customer_name": f"{request.user.first_name} {request.user.last_name}".strip() or "Customer",
            "customer_email": request.user.email
        }
        serializer = PaymentInitResponseSerializer(response_data)

        return ResponseHandler.success_response(
            message="Payment gateway intent initialized.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class RazorpayWebhookView(APIView):
    """
    🪝 VIEW 2: SECURITY SIGNED WEBHOOK RECEIVER
    Listens directly to server updates from Razorpay to finalize the workflow.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body.decode('utf-8')
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')

        webhook_secret = settings.PAYMENTS.get("RAZORPAY", {}).get("WEBHOOK_SECRET", "")

        # 🔐 Cryptographic signature verification
        try:
            razorpay_client.utility.verify_webhook_signature(
                payload,
                signature,
                webhook_secret
            )
        except Exception:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        event_data = json.loads(payload)
        event_type = event_data.get('event')

        if event_type == "order.paid":
            payment_entity = event_data['payload']['payment']['entity']
            razorpay_order_id = payment_entity['order_id']
            razorpay_payment_id = payment_entity['id']

            with transaction.atomic():
                try:
                    # 🔒 Lock and update the transaction record
                    txn = Transaction.objects.select_for_update().get(
                        gateway_order_id=razorpay_order_id
                    )

                    if txn.status == TransactionStatus.PENDING:
                        txn.status = TransactionStatus.SUCCESS
                        txn.gateway_transaction_id = razorpay_payment_id
                        txn.gateway_signature = signature
                        txn.raw_response_snapshot = event_data
                        txn.save()

                        # 🔒 Lock and update the parent order
                        order = Order.objects.select_for_update().get(id=txn.order_id)

                        order.status = OrderStatus.COMPLETED
                        order.save()

                        
                        transaction.on_commit(
                            lambda: generate_and_send_invoice_task.delay(order.id)
                        )

                except Transaction.DoesNotExist:
                    pass
                except Order.DoesNotExist:
                    pass

        return HttpResponse(status=status.HTTP_200_OK)