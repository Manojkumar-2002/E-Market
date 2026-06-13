# config/settings/__init__.py
import os
import environ
from pathlib import Path

# 1. Resolve base directory to find the .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 2. Initialize environ and read the .env file globally
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# 3. Determine current environment status (default to development)
ENVIRONMENT = env.str("ENVIRONMENT", default="development").lower()

# 4. Dynamically import the matching settings profile namespace
if ENVIRONMENT == "production":
    from .production import *
else:
    from .development import *