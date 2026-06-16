import logging
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from django.conf import settings

logger = logging.getLogger(__name__)

def send_email(
    *,
    subject: str,
    to,
    context: dict,
    template_html: str,
    template_text: str = None,
    attachments: list = None,
    inline_images: list = None,
    from_email: str = None,
    cc: list = None,
    bcc: list = None,
    fail_silently=False,
):
    """
    Optimized Django 6.0 email sender:
        - HTML email (required)
        - Text fallback (optional)
        - Inline images (CID)
        - Attachments
        - CC/BCC support
        - Logging + try/except
        - No over-engineering
    """
    
    try:
        # --- Render Templates ---
        html_body = render_to_string(template_html, context)
        text_body = render_to_string(template_text, context) if template_text else ""
        
        # --- Build Message ---
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body or html_body,
            from_email=from_email or settings.EMAIL_SENDER_DEFAULT,
            to=[to] if isinstance(to, str) else to,
            cc=cc or [],
            bcc=bcc or [],
        )
        
        msg.attach_alternative(html_body, "text/html")
        
        # --- Inline CID Images ---
        if inline_images:
            for img in inline_images:
                mime_img = MIMEImage(
                    img["data"],
                    _subtype=img["mime"].split("/")[-1],
                )
                mime_img.add_header("Content-ID", f"<{img['cid']}>")
                mime_img.add_header(
                    "Content-Disposition",
                    "inline",
                    filename=img["filename"],
                )
                msg.attach(mime_img)
                
        # --- Normal Attachments ---
        if attachments:
            for att in attachments:
                msg.attach(att["filename"], att["data"], att["mime"])
                
        # --- Send Email ---
        connection = get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            timeout=getattr(settings, "EMAIL_TIMEOUT", 30),
        )
        
        sent = msg.send(fail_silently=fail_silently)
        connection.close()
        
        logger.info(f"[EMAIL] Sent email to={to} count={sent}")
        return True

    except Exception as e:
        logger.error(f"[EMAIL] Failed to send: {e}", exc_info=True)
        if not fail_silently:
            raise
        return False