# config/settings/components/email.py

def get_email_config(env):
    """
    Configures the SMTP email backend settings.
    These map directly to the custom `send_email` utility and Django's core mail handler.
    """
    return {
        # Core Django email backend 
        "EMAIL_BACKEND": env.str("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"),
        
        # 🌐 SMTP Server Connection Details
        "EMAIL_HOST": env.str("EMAIL_HOST", default="smtp.gmail.com"),
        "EMAIL_PORT": env.int("EMAIL_PORT", default=587),
        
        # 🔒 Security Protocols
        "EMAIL_USE_TLS": env.bool("EMAIL_USE_TLS", default=True),
        "EMAIL_USE_SSL": env.bool("EMAIL_USE_SSL", default=False),
        
        # 🔑 Authentication Credentials
        "EMAIL_HOST_USER": env.str("EMAIL_HOST_USER", default=""),
        "EMAIL_HOST_PASSWORD": env.str("EMAIL_HOST_PASSWORD", default=""),
        
        # ⏱️ Custom settings strictly required by your `send_email` utility
        "EMAIL_TIMEOUT": env.int("EMAIL_TIMEOUT", default=30),
        "EMAIL_SENDER_DEFAULT": env.str(
            "EMAIL_SENDER_DEFAULT", 
            default="E-Cart Support <noreply@ecart.com>"
        ),
    }