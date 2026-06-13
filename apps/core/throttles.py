# apps/core/throttles.py
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class DisjointAnonThrottle(AnonRateThrottle):
    cache_alias = "throttle"

class DisjointUserThrottle(UserRateThrottle):
    cache_alias = "throttle"