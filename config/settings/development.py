import environ
from .base import *
from .components.core import get_core_config
from .components.database import get_database_config
from .components.rest_framework import get_jwt_auth_config  # 🌟 Import the new auth component

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# Fetch Configurations
core_component = get_core_config(env)
db_component = get_database_config(env)
auth_component = get_jwt_auth_config(env)  # 🌟 Fetch auth dictionary

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

# Security & Docs Component Mappings
REST_FRAMEWORK = auth_component["REST_FRAMEWORK"]
SIMPLE_JWT = auth_component["SIMPLE_JWT"]
SPECTACULAR_SETTINGS = auth_component["SPECTACULAR_SETTINGS"]