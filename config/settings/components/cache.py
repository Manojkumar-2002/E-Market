# config/settings/components/cache.py

def get_cache_config(env):
    """
    Configures an isolated multi-database Redis caching architecture 
    to separate general data, throttling blocks, and user sessions.
    """
    # 1. Fetch individual connection routing tokens
    cache_url = env.str("REDIS_CACHE_URL", default="redis://redis:6379/1")
    throttle_url = env.str("REDIS_THROTTLE_URL", default="redis://redis:6379/2")
    session_url = env.str("REDIS_SESSION_URL", default="redis://redis:6379/3")

    # Reusable connection driver timeout options
    base_options = {
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
    }

    return {
        "CACHES": {
            # 👑 The Default app-wide data cache (Product lists, metadata, etc.)
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": cache_url,
                "OPTIONS": base_options,
            },
           
            "throttle": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": throttle_url,
                "OPTIONS": base_options,
            },
            # 🔑 Protected database dedicated strictly to login session persistence
            "session": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": session_url,
                "OPTIONS": base_options,
            },
        }
    }