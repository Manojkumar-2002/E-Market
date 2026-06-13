import time
import logging
from django.core.cache import cache
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Enterprise Centralized Class-Driven Cache Registry.
    Uses dynamic blueprints to eliminate string duplication across domains.
    """

    class CacheBlueprint:
        """Structural engine that generates blueprints uniformly."""
        def __init__(self, domain: str, scope_prefix: str):
            # The escaped {{scope_id}} allows us to call .format() later in the lifecycle
            self.VERSION = f"v_track:{domain}:{scope_prefix}_{{scope_id}}"
            self.DATA = f"mv{{master_version}}:{domain}:{scope_prefix}_{{scope_id}}:v{{sub_version}}:{{details}}"

    # 🌟 CENTRAL REGISTRY SCHEMAS
    Products = CacheBlueprint(domain="catalog", scope_prefix="cat")
    Carts    = CacheBlueprint(domain="shopping_basket", scope_prefix="user")
    Orders   = CacheBlueprint(domain="order_pipeline", scope_prefix="track")

    # --- SYSTEM MASTER SWITCH CONTROL ---
    
    @classmethod
    def get_global_app_version(cls) -> int:
        """Retrieves system-wide master version root."""
        try:
            fallback = int(time.time())
            return cache.get_or_set("v_track:sys:master_switch", fallback, timeout=None)
        except (RedisError, Exception) as e:
            logger.warning(f"Cache registry failure reading master switch: {str(e)}")
            return int(time.time())

    @classmethod
    def bump_global_app_version(cls) -> None:
        """Bumps system master switch, instantly rolling over the entire app's cache."""
        try:
            cache.incr("v_track:sys:master_switch")
            logger.info("!!! CENTRAL REGISTRY: Global app master version advanced !!!")
        except ValueError:
            cache.set("v_track:sys:master_switch", int(time.time()), timeout=None)
        except (RedisError, Exception) as e:
            logger.error(f"Failed central master reset: {str(e)}")

    # --- REGISTRY RESOLUTION & VERSIONING ---

    @classmethod
    def _resolve_target_blueprint(cls, key_token: str) -> CacheBlueprint:
        """
        Dynamically extracts the matched Blueprint instance from the manager context.
        Guards against typos by validating properties.
        """
        class_target = key_token.strip().title()
        if not hasattr(cls, class_target):
            raise KeyError(f"Registry Error: '{class_target}' is not an authorized cache blueprint domain.")
            
        return getattr(cls, class_target)

    @classmethod
    def get_version(cls, key_token: str, scope_id: str | int = None) -> int:
        """Fetches the active sub-scope version tracking integer using our blueprint templates."""
        blueprint = cls._resolve_target_blueprint(key_token)
        cleaned_scope = str(scope_id) if scope_id else "global"
        
        # Format the isolated tracking key name
        version_key = blueprint.VERSION.format(scope_id=cleaned_scope)
        
        try:
            return cache.get_or_set(version_key, int(time.time()), timeout=None)
        except (RedisError, Exception) as e:
            logger.warning(f"Registry version read failure for {key_token}: {str(e)}")
            return int(time.time())

    @classmethod
    def bump_version(cls, key_token: str, scope_id: str | int = None) -> None:
        """Bumps the sub-scope version tracker, cutting off access to stale keys."""
        blueprint = cls._resolve_target_blueprint(key_token)
        cleaned_scope = str(scope_id) if scope_id else "global"
        version_key = blueprint.VERSION.format(scope_id=cleaned_scope)
        
        try:
            cache.incr(version_key)
            logger.info(f"Registry advanced version for blueprint path: {version_key}")
        except ValueError:
            try:
                cache.set(version_key, int(time.time()), timeout=None)
            except (RedisError, Exception):
                pass
        except (RedisError, Exception) as e:
            logger.error(f"Critical error incrementing inner blueprint lane {key_token}: {str(e)}")

    # --- HIGH-PERFORMANCE DATA KEY GENERATOR ---

    @classmethod
    def build_registry_key(cls, key_token: str, scope_id: str | int = None, details: str = "list") -> str:
        """
        Builds complete data keys by evaluating master and sub-versions against blueprints.
        """
        blueprint = cls._resolve_target_blueprint(key_token)
        
        # 1. Gather live dual-layer versions
        master_v = cls.get_global_app_version()
        sub_v = cls.get_version(key_token, scope_id)
        cleaned_scope = str(scope_id) if scope_id else "global"
        
        # 2. Extract and format the strict data string layout
        return blueprint.DATA.format(
            master_version=master_v,
            scope_id=cleaned_scope,
            sub_version=sub_v,
            details=details
        )

    # --- CORE SAFE READ/WRITE WRAPPERS ---

    @classmethod
    def get_cached_data(cls, key: str) -> any:
        try: return cache.get(key)
        except (RedisError, Exception): return None

    @classmethod
    def set_cached_data(cls, key: str, data: any, timeout: int = 86400) -> bool:
        try:
            cache.set(key, data, timeout=timeout)
            return True
        except (RedisError, Exception): return False