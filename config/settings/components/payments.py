# settings/components/payments.py

def get_payment_config(env):
    """
    💳 POLYMORPHIC MERCHANT GATEWAY MATRIX COMPONENT:
    Organizes API access credentials inside distinct gateway namespaces.
    Allows easy expansion for Stripe, PayPal, etc., down the line.
    """
    return {
        "PAYMENTS": {
            "RAZORPAY": {
                "KEY_ID": env.str("RAZORPAY_KEY_ID", default=""),
                "KEY_SECRET": env.str("RAZORPAY_KEY_SECRET", default=""),
                "WEBHOOK_SECRET": env.str("RAZORPAY_WEBHOOK_SECRET", default=""),
            },
            # 💡 You can cleanly add alternative processors here later:
            # "STRIPE": {
            #     "API_KEY": env.str("STRIPE_API_KEY", default=""),
            #     "WEBHOOK_SECRET": env.str("STRIPE_WEBHOOK_SECRET", default=""),
            # }
        }
    }