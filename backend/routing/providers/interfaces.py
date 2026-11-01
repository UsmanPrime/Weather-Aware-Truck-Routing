from datetime import datetime
from typing import Protocol

from routing.domain.types import Coordinate, ForecastSeries, RouteDiscovery


class RoutingProvider(Protocol):
    def discover(
        self, origin: Coordinate, destination: Coordinate, departure_at: datetime
    ) -> RouteDiscovery: ...


class ForecastProvider(Protocol):
    def forecast(self, positions: tuple[Coordinate, ...]) -> tuple[ForecastSeries, ...]: ...
