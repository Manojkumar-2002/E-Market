import environ
from .base import *
from .components.core import get_core_config
from .components.database import get_database_config
from .components.rest_framework import get_jwt_auth_config
from .components.cache import get_cache_config
from .components.celery_config import get_celery_config
from .components.payments import get_payment_config
from .components.email import get_email_config

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# Fetch Configurations
core_component = get_core_config(env)
db_component = get_database_config(env)
auth_component = get_jwt_auth_config(env)
cache_component = get_cache_config(env)
celery_component = get_celery_config(env)
payment_component = get_payment_config(env)
email_component = get_email_config(env)


# Core Mappings
SECRET_KEY = core_component["SECRET_KEY"]
DEBUG = core_component["DEBUG"]
ALLOWED_HOSTS = core_component["ALLOWED_HOSTS"]
CSRF_TRUSTED_ORIGINS = core_component["CSRF_TRUSTED_ORIGINS"]
CORS_ALLOWED_ORIGINS = core_component["CORS_ALLOWED_ORIGINS"]
TIME_ZONE = core_component.get("TIME_ZONE", "UTC")
LANGUAGE_CODE = core_component.get("LANGUAGE_CODE", "en-us")

# Complex Structs Mappings
DATABASES = db_component["DATABASES"]

CACHES = cache_component["CACHES"]
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"

# Security & Docs Component Mappings
REST_FRAMEWORK = auth_component["REST_FRAMEWORK"]
SIMPLE_JWT = auth_component["SIMPLE_JWT"]
SPECTACULAR_SETTINGS = auth_component["SPECTACULAR_SETTINGS"]

CELERY_BROKER_URL = celery_component["CELERY_BROKER_URL"]
CELERY_RESULT_BACKEND = celery_component["CELERY_RESULT_BACKEND"]
CELERY_TASK_IGNORE_RESULT = celery_component["CELERY_TASK_IGNORE_RESULT"]
CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED = celery_component["CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED"] 
CELERY_TASK_ACKS_LATE = celery_component["CELERY_TASK_ACKS_LATE"]
CELERY_TASK_REJECT_ON_WORKER_LOST = celery_component["CELERY_TASK_REJECT_ON_WORKER_LOST"]
CELERY_RESULT_EXPIRES = celery_component["CELERY_RESULT_EXPIRES"]
CELERY_TIMEZONE = celery_component["CELERY_TIMEZONE"]
CELERY_ENABLE_UTC = celery_component["CELERY_ENABLE_UTC"]
CELERY_QUEUES = celery_component["CELERY_QUEUES"] 
CELERY_TASK_ROUTES = celery_component["CELERY_TASK_ROUTES"]

PAYMENTS = payment_component["PAYMENTS"]


EMAIL_BACKEND = email_component["EMAIL_BACKEND"]
EMAIL_HOST = email_component["EMAIL_HOST"]
EMAIL_PORT = email_component["EMAIL_PORT"]
EMAIL_USE_TLS = email_component["EMAIL_USE_TLS"]
EMAIL_USE_SSL = email_component["EMAIL_USE_SSL"]
EMAIL_HOST_USER = email_component["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = email_component["EMAIL_HOST_PASSWORD"]
EMAIL_TIMEOUT = email_component["EMAIL_TIMEOUT"]
EMAIL_SENDER_DEFAULT = email_component["EMAIL_SENDER_DEFAULT"]