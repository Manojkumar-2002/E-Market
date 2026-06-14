from django.urls import path
from apps.payments.views import InitializePaymentView, RazorpayWebhookView

app_name = "payments"

urlpatterns = [
    # 💳 1. INTENT INITIALIZER
    # Invoked when the user clicks the "Pay Now" button on the frontend checkout summary screen.
    path(
        "orders/<uuid:order_id>/initiate/", 
        InitializePaymentView.as_view(), 
        name="payment_initiate"
    ),
    
    # 🪝 2. SECURITY WEBHOOK RECEIVER
    # This is the public endpoint you register inside your Razorpay Developer Dashboard.
    # Razorpay's background servers invoke this asynchronously to settle the transaction records.
    path(
        "webhook/razorpay/", 
        RazorpayWebhookView.as_view(), 
        name="razorpay_webhook"
    ),
]