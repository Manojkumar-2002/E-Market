import environ
from .base import *
from .components.core import get_core_config
from .components.database import get_database_config

# Initialize django-environ
env = environ.Env()

# Read the .env file using the BASE_DIR path inherited from base.py
environ.Env.read_env(BASE_DIR / ".env")

# 1. Fetch Core & Database Dict Components
core_component = get_core_config(env)
db_component = get_database_config(env)

# 2. Map Constants Directly to Global Namespace
SECRET_KEY = core_component["SECRET_KEY"]
DEBUG = core_component["DEBUG"]
ALLOWED_HOSTS = core_component["ALLOWED_HOSTS"]
CSRF_TRUSTED_ORIGINS = core_component["CSRF_TRUSTED_ORIGINS"]
CORS_ALLOWED_ORIGINS = core_component["CORS_ALLOWED_ORIGINS"]

# 3. Extract Complex Dictionary Structs
DATABASES = db_component["DATABASES"]
