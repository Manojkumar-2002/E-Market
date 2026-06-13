def get_core_config(env):
    """
    Component for core app settings. 
    Handles strict key retrieval and automatic comma-separated string-to-list casting.
    """
    return {
        "SECRET_KEY": env.str("SECRET_KEY"),
        "DEBUG": env.bool("DEBUG", default=False),
        "ALLOWED_HOSTS": env.list("ALLOWED_HOSTS", default=["yourdomain.com"]),
        "CSRF_TRUSTED_ORIGINS": env.list("CSRF_TRUSTED_ORIGINS", default=[]),
        "CORS_ALLOWED_ORIGINS": env.list("CORS_ALLOWED_ORIGINS", default=[]),
        "TIME_ZONE": env.str("TIME_ZONE", default="UTC"),
        "LANGUAGE_CODE": env.str("LANGUAGE_CODE", default="en-us")
    }