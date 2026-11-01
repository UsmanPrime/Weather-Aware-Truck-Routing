"""Hourly model forecasts. Rain + showers are liquid; snowfall is snow depth, not SWE."""

from datetime import UTC, datetime, timedelta

from routing.domain.risk import normalize_weather
from routing.domain.types import Coordinate, ForecastSeries, HourlyForecast

from .errors import invalid_payload
from .http import HttpTransport, JsonTransport

ENDPOINT = "https://api.open-meteo.com/v1/forecast"
VARIABLES = ("wind_speed_10m", "rain", "showers", "snowfall")
UNITS = {
    "time": "unixtime",
    "wind_speed_10m": "km/h",
    "rain": "mm",
    "showers": "mm",
    "snowfall": "cm",
}
MAX_BATCH_SIZE = 25


def parse_forecasts(
    payload: object, positions: tuple[Coordinate, ...], retrieved_at: datetime
) -> tuple[ForecastSeries, ...]:
    try:
        items = payload if isinstance(payload, list) else [payload]
        if len(items) != len(positions):
            raise ValueError("Mismatched batch size")
        results = []
        for item, requested in zip(items, positions, strict=True):
            if item["utc_offset_seconds"] != 0 or any(
                item["hourly_units"].get(key) != value for key, value in UNITS.items()
            ):
                raise ValueError("Unexpected units/timezone")
            grid = Coordinate(item["latitude"], item["longitude"])
            # Grid cells differ from requested coordinates. Guard reordered/distant responses.
            lon_difference = abs((grid.longitude - requested.longitude + 180) % 360 - 180)
            if abs(grid.latitude - requested.latitude) > 1 or lon_difference > 1:
                raise ValueError("Response does not match requested location order")
            hourly = item["hourly"]
            times = hourly["time"]
            if not isinstance(times, list) or not 1 <= len(times) <= 16 * 24:
                raise ValueError("Invalid forecast horizon")
            if any(
                not isinstance(hourly[key], list) or len(hourly[key]) != len(times)
                for key in VARIABLES
            ):
                raise ValueError("Truncated hourly arrays")
            hours = []
            for i, timestamp in enumerate(times):
                if type(timestamp) is not int:
                    raise ValueError("Expected Unix UTC timestamps")
                valid_at = datetime.fromtimestamp(timestamp, UTC)
                if hours and valid_at <= hours[-1].valid_at:
                    raise ValueError("Unordered hourly timestamps")
                hours.append(
                    HourlyForecast(
                        valid_at,
                        valid_at - timedelta(hours=1),
                        valid_at,
                        normalize_weather(
                            wind_kmh=hourly["wind_speed_10m"][i],
                            rain_mm=hourly["rain"][i],
                            showers_mm=hourly["showers"][i],
                            snow_cm=hourly["snowfall"][i],
                        ),
                    )
                )
            results.append(ForecastSeries(requested, grid, retrieved_at, tuple(hours)))
        return tuple(results)
    except (KeyError, TypeError, ValueError, IndexError, OverflowError, OSError, AttributeError):
        raise invalid_payload("open_meteo") from None


class OpenMeteo:
    def __init__(self, transport: JsonTransport | None = None):
        self.transport = transport or HttpTransport()

    def forecast(self, positions: tuple[Coordinate, ...]) -> tuple[ForecastSeries, ...]:
        if not 1 <= len(positions) <= MAX_BATCH_SIZE:
            raise ValueError(f"Forecast batches must contain 1–{MAX_BATCH_SIZE} coordinates")
        params = {
            "latitude": ",".join(str(point.latitude) for point in positions),
            "longitude": ",".join(str(point.longitude) for point in positions),
            "hourly": ",".join(VARIABLES),
            "timezone": "GMT",
            "timeformat": "unixtime",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "forecast_days": "7",
        }
        payload = self.transport.get_json("open_meteo", ENDPOINT, params)
        return parse_forecasts(payload, positions, datetime.now(UTC))
