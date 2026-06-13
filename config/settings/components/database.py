def get_database_config(env):
    """
    Component explicitly handling Database setup.
    """
    return {
        "DATABASES": {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": env.str("DB_NAME"),
                "USER": env.str("DB_USER"),
                "PASSWORD": env.str("DB_PASSWORD"),
                "HOST": env.str("DB_HOST"),
                "PORT": env.int("DB_PORT", default=5432),
                "CONN_MAX_AGE": 0,
                "CONN_HEALTH_CHECKS": True,
            }
        }
    }