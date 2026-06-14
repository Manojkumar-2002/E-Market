# apps/core/utils/razorpay_client.py
import razorpay
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Extract the Razorpay sub-dict safely from the Django settings registry
razorpay_config = settings.PAYMENTS.get("RAZORPAY", {})

key_id = razorpay_config.get("KEY_ID")
key_secret = razorpay_config.get("KEY_SECRET")

# 🛡️ SYSTEM INTEGRITY GUARDRAILS
if not key_id:
    raise ImproperlyConfigured("RAZORPAY 'KEY_ID' is missing from the PAYMENTS configuration matrix.")
if not key_secret:
    raise ImproperlyConfigured("RAZORPAY 'KEY_SECRET' is missing from the PAYMENTS configuration matrix.")



client = razorpay.Client(auth=(key_id, key_secret))