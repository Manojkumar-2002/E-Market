import environ
from .base import *
from .components.core import get_core_config
from .components.database import get_database_config
from .components.rest_framework import get_jwt_auth_config  # 🌟 Import the new auth component
from .components.cache import get_cache_config

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# Fetch Configurations
core_component = get_core_config(env)
db_component = get_database_config(env)
auth_component = get_jwt_auth_config(env)
cache_component = get_cache_config(env)

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