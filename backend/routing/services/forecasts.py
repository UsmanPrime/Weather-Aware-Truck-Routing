from datetime import UTC, datetime
from time import monotonic

from django.core.cache import cache

from routing.domain.types import Coordinate
from routing.providers.errors import ProviderError
from routing.providers.http import HttpTransport
from routing.providers.open_meteo import MAX_BATCH_SIZE, OpenMeteo

from .cache import cache_key, reserve


def load_forecasts(positions: tuple[Coordinate, ...], *, provider=None, deadline=None):
    """Exact-coordinate reuse. Failed batches stay missing; no substitution or stale fallback."""
    deadline = deadline or monotonic() + 20
    found, missing, warnings = {}, [], []
    day = datetime.now(UTC).date().isoformat()
    for position in dict.fromkeys(positions):
        key = cache_key("weather", (position, day))
        series = cache.get(key) if provider is None else None
        if series is None:
            missing.append(position)
        else:
            found[position] = series
    for start in range(0, len(missing), MAX_BATCH_SIZE):
        batch = tuple(missing[start : start + MAX_BATCH_SIZE])
        remaining = deadline - monotonic()
        try:
            if remaining <= 0:
                raise ProviderError(
                    "open_meteo", "deadline", "Weather request deadline reached.", 504, True
                )
            if provider is None:
                reserve("open_meteo", len(batch))
            adapter = provider or OpenMeteo(HttpTransport(timeout_s=min(8, remaining)))
            for series in adapter.forecast(batch):
                found[series.requested_position] = series
                if provider is None:
                    cache.set(cache_key("weather", (series.requested_position, day)), series, 900)
        except ProviderError as error:
            warnings.append({"code": error.code, "message": error.message})
    return found, warnings
