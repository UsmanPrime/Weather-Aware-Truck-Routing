"""Independent coverage lookup: heatmap completeness never gates route evaluation."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from .types import ForecastSeries, Weather


@dataclass(frozen=True)
class ForecastAtTime:
    weather: Weather
    wind_valid_at: datetime | None
    precipitation_start: datetime | None
    precipitation_end: datetime | None


def forecast_at(series: ForecastSeries, instant: datetime) -> ForecastAtTime:
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Forecast lookup requires an aware instant")
    wind = min(series.hours, key=lambda hour: abs(hour.valid_at - instant), default=None)
    if wind and (
        abs(wind.valid_at - instant) > timedelta(minutes=30)
        or instant < series.hours[0].valid_at
        or instant > series.hours[-1].valid_at
    ):
        wind = None
    precipitation = next(
        (
            hour
            for hour in series.hours
            if hour.precipitation_start < instant <= hour.precipitation_end
        ),
        None,
    )
    return ForecastAtTime(
        Weather(
            wind.weather.wind_mph if wind else None,
            precipitation.weather.rain_in_per_hr if precipitation else None,
            precipitation.weather.snow_in_per_hr if precipitation else None,
        ),
        wind.valid_at if wind else None,
        precipitation.precipitation_start if precipitation else None,
        precipitation.precipitation_end if precipitation else None,
    )
