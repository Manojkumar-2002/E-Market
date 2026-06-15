import logging
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML

logger = logging.getLogger(__name__)

def generate_pdf_from_template(template_name: str, context: dict = None) -> bytes:
    """
    Generic PDF generator using WeasyPrint.
    Takes an HTML template path and context dict, returns PDF binary data.
    """
    if context is None:
        context = {}

    try:
        # 1. Render Django HTML template with dynamic context
        html_string = render_to_string(template_name, context)

        # 2. Define base_url so WeasyPrint can fetch static files (images, css)
        # Assuming you have a BASE_URL setting, fallback to localhost for local dev
        base_url = getattr(settings, 'BASE_URL', 'https://psychic-space-waddle-4jg6xq4rwxwxcqwjg-8000.app.github.dev')

        # 3. Generate PDF bytes
        pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()

        return pdf_bytes

    except Exception as e:
        logger.error(f"[PDF_SERVICE] Failed to generate PDF from {template_name}: {e}", exc_info=True)
        # Re-raise so the calling Celery task knows it failed and can retry
        raise