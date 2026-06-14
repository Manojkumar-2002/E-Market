from rest_framework import serializers
from apps.payments.models import Transaction


class PaymentInitResponseSerializer(serializers.Serializer):
    """
    👑 GATEWAY RESPONSE SNAPSHOT:
    Standardizes the structural payload returned to the frontend 
    to spin up the Razorpay Checkout overlay or forms.
    """
    gateway_order_id = serializers.CharField()
    amount = serializers.IntegerField(help_text="Value converted to lowest currency units (paise)")
    currency = serializers.CharField()
    key_id = serializers.CharField()
    customer_name = serializers.CharField()
    customer_email = serializers.EmailField()


class TransactionAuditSerializer(serializers.ModelSerializer):
    """
    📋 TRANSACTION JOURNAL SERIALIZER:
    Used for order detail panels or administrative audit dashboards.
    """
    class Meta:
        model = Transaction
        fields = [
            'id', 'gateway', 'gateway_order_id', 'gateway_transaction_id',
            'amount', 'status', 'error_code', 'created_at', 'created_by'
        ]