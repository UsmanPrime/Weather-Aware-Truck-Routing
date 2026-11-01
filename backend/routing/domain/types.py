from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from math import isfinite


class Risk(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float

    def __post_init__(self):
        if (
            isinstance(self.latitude, bool)
            or isinstance(self.longitude, bool)
            or not isfinite(self.latitude)
            or not isfinite(self.longitude)
            or not -90 <= self.latitude <= 90
            or not -180 <= self.longitude <= 180
        ):
            raise ValueError("Invalid geographic coordinate")


@dataclass(frozen=True)
class Weather:
    wind_mph: float | None
    rain_in_per_hr: float | None
    snow_in_per_hr: float | None


@dataclass(frozen=True)
class HourlyForecast:
    valid_at: datetime
    precipitation_start: datetime
    precipitation_end: datetime
    weather: Weather


@dataclass(frozen=True)
class ForecastSeries:
    requested_position: Coordinate
    grid_position: Coordinate
    retrieved_at: datetime
    hours: tuple[HourlyForecast, ...]


@dataclass(frozen=True)
class Notice:
    code: str
    severity: str


@dataclass(frozen=True)
class RouteSpan:
    offset: int
    length_m: float
    duration_s: float
    dynamic_speed_m_per_s: float | None
    notices: tuple[Notice, ...] = ()


@dataclass(frozen=True)
class RouteSection:
    id: str
    geometry: tuple[Coordinate, ...]
    distance_m: float
    duration_s: float
    travel_duration_s: float
    spans: tuple[RouteSpan, ...]
    notices: tuple[Notice, ...]


@dataclass(frozen=True)
class ProviderRoute:
    id: str
    sections: tuple[RouteSection, ...]
    notices: tuple[Notice, ...]

    @property
    def distance_m(self) -> float:
        return sum(section.distance_m for section in self.sections)

    @property
    def duration_s(self) -> float:
        return sum(section.duration_s for section in self.sections)


@dataclass(frozen=True)
class RouteDiscovery:
    routes: tuple[ProviderRoute, ...]
    returned_count: int
    duplicate_count: int
