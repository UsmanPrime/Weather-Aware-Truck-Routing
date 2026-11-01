"""Small per-process TTL cache and conservative free-service budgets; one production worker."""

from datetime import UTC, datetime
from hashlib import sha256
from threading import Lock

from django.core.cache import cache

from routing.providers.errors import ProviderError

_budget_lock = Lock()
_usage = {}
LIMITS = {"ors": (10, 100), "pelias": (20, 200), "open_meteo": (150, 3000)}


def cache_key(namespace: str, value: object) -> str:
    return namespace + ":" + sha256(repr(value).encode()).hexdigest()


def reserve(provider: str, cost: int = 1):
    now = datetime.now(UTC)
    minute, day = LIMITS[provider]
    buckets = [
        (f"budget:{provider}:minute:{now:%Y%m%d%H%M}", minute, 70),
        (f"budget:{provider}:day:{now:%Y%m%d}", day, 86460),
    ]
    with _budget_lock:
        for period in ("minute", "day"):
            prefix = f"budget:{provider}:{period}:"
            active = next(key for key, _, _ in buckets if key.startswith(prefix))
            for key in list(_usage):
                if key.startswith(prefix) and key != active:
                    del _usage[key]
        if any(_usage.get(key, 0) + cost > limit for key, limit, _ in buckets):
            raise ProviderError(
                provider,
                "local_budget",
                "Free-service request budget reached. Try later.",
                429,
                True,
                60,
            )
        for key, _, _ttl in buckets:
            _usage[key] = _usage.get(key, 0) + cost


def cached_call(namespace: str, value: object, ttl: int, loader, provider: str):
    key = cache_key(namespace, value)
    result = cache.get(key)
    if result is not None:
        return result
    reserve(provider, 2 if provider == "ors" else 1)
    result = loader()
    cache.set(key, result, ttl)
    return result
