from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest

from routing.domain.forecast import forecast_at
from routing.domain.types import Coordinate
from routing.providers.errors import ProviderError
from routing.providers.here import HereRouting, decode_geometry, parse_routes
from routing.providers.open_meteo import OpenMeteo, parse_forecasts

NOW = datetime(2026, 11, 1, tzinfo=UTC)
POSITION = Coordinate(41, -87)


class SyntheticTransport:
    """Returns explicitly synthetic fixtures, never performs network access."""

    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_json(self, provider, endpoint, params):
        self.calls.append((provider, endpoint, params))
        return self.payload


def test_here_request_and_official_totals(here_payload):
    transport = SyntheticTransport(here_payload)
    discovery = HereRouting("synthetic-test-key", transport).discover(
        POSITION, Coordinate(40, -86), NOW
    )
    params = transport.calls[0][2]
    assert params["transportMode"] == "truck"
    assert params["alternatives"] == "2"
    assert params["spans"] == "length,duration,dynamicSpeedInfo,notices"
    assert "weight" not in params  # cargo is not gross vehicle weight
    assert discovery.returned_count == 1
    assert discovery.routes[0].distance_m == 30000
    assert discovery.routes[0].duration_s == 2400
    section = discovery.routes[0].sections[0]
    assert section.travel_duration_s == 2300
    assert sum(span.duration_s for span in section.spans) == 2300
    assert section.geometry[0] == POSITION
    assert section.notices[0].severity == "critical"


def test_decode_official_here_documentation_vector():
    # Public HERE flexible-polyline reference example, not a discovered truck route.
    geometry = decode_geometry("BFoz5xJ67i1B1B7PzIhaxL7Y")
    assert geometry[0].latitude == pytest.approx(50.10228)
    assert geometry[0].longitude == pytest.approx(8.69821)
    assert len(geometry) == 4


def test_duplicate_geometries_are_not_alternatives(here_payload):
    duplicate = deepcopy(here_payload["routes"][0])
    duplicate["id"] = "synthetic-duplicate"
    here_payload["routes"].append(duplicate)
    result = parse_routes(here_payload)
    assert result.returned_count == 2
    assert len(result.routes) == 1
    assert result.duplicate_count == 1


def test_three_distinct_geometries_preserved(here_payload):
    import flexpolyline

    for i in (1, 2):
        alternative = deepcopy(here_payload["routes"][0])
        alternative["id"] = f"synthetic-alternative-{i}"
        alternative["sections"][0]["polyline"] = flexpolyline.encode(
            [(41, -87), (41 + i, -86), (40, -85)]
        )
        here_payload["routes"].append(alternative)
    assert len(parse_routes(here_payload).routes) == 3


@pytest.mark.parametrize("payload", [None, {}, {"routes": [None]}, {"routes": "invalid"}])
def test_here_malformed_payload_is_structured(payload):
    with pytest.raises(ProviderError, match="invalid_payload"):
        parse_routes(payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("polyline", "!"),
        ("polyline", "B"),
        ("summary", {"length": -1, "duration": 1}),
        ("spans", [{"offset": 99, "length": 1, "duration": 1}]),
        ("spans", [{"offset": 1, "length": 1, "duration": 1}]),
    ],
)
def test_here_invalid_section_rejected(here_payload, field, value):
    here_payload["routes"][0]["sections"][0][field] = value
    with pytest.raises(ProviderError):
        parse_routes(here_payload)


def test_no_routes_and_no_credentials():
    assert parse_routes({"routes": []}).routes == ()
    with pytest.raises(ProviderError, match="missing_credentials"):
        HereRouting("").discover(POSITION, Coordinate(40, -86), NOW)


def test_span_notices_preserved(here_payload):
    here_payload["routes"][0]["sections"][0]["spans"][0]["notices"] = [
        {"code": "synthetic-span-restriction", "severity": "critical"}
    ]
    route = parse_routes(here_payload).routes[0]
    assert route.sections[0].spans[0].notices[0].code == "synthetic-span-restriction"


def test_naive_departure_rejected_before_http():
    with pytest.raises(ValueError, match="timezone-aware"):
        HereRouting("synthetic-test-key").discover(
            POSITION, Coordinate(40, -86), datetime(2026, 11, 1)
        )


def test_forecast_request_units_intervals_and_nulls(weather_payload):
    transport = SyntheticTransport(weather_payload)
    series = OpenMeteo(transport).forecast((POSITION,))[0]
    params = transport.calls[0][2]
    assert params["timezone"] == "GMT"
    assert params["timeformat"] == "unixtime"
    assert "precipitation" not in params["hourly"]  # no total-precipitation double count
    first = series.hours[0]
    assert first.valid_at == NOW
    assert first.precipitation_start == NOW - timedelta(hours=1)
    assert first.precipitation_end == NOW
    assert first.weather.rain_in_per_hr == pytest.approx(0.2)
    assert first.weather.snow_in_per_hr == pytest.approx(1)
    assert series.hours[-1].weather.rain_in_per_hr is None


def test_batch_order_and_grid_positions(weather_payload):
    other = deepcopy(weather_payload)
    other.update(latitude=39, longitude=-90)
    positions = (POSITION, Coordinate(39, -90))
    result = parse_forecasts([weather_payload, other], positions, NOW)
    assert tuple(item.requested_position for item in result) == positions
    with pytest.raises(ProviderError):
        parse_forecasts([other, weather_payload], positions, NOW)


@pytest.mark.parametrize("change", ["units", "timezone", "truncated", "unordered", "empty"])
def test_forecast_schema_errors(weather_payload, change):
    if change == "units":
        weather_payload["hourly_units"]["snowfall"] = "mm"
    elif change == "timezone":
        weather_payload["utc_offset_seconds"] = 3600
    elif change == "truncated":
        weather_payload["hourly"]["rain"] = []
    elif change == "unordered":
        weather_payload["hourly"]["time"].reverse()
    else:
        weather_payload["hourly"]["time"] = []
    with pytest.raises(ProviderError, match="invalid_payload"):
        parse_forecasts(weather_payload, (POSITION,), NOW)


@pytest.mark.parametrize("positions", [(), (POSITION,) * 26])
def test_batch_limits(positions):
    with pytest.raises(ValueError):
        OpenMeteo().forecast(positions)


def test_forecast_lookup_exact_interval_and_nearest_wind(weather_payload):
    series = parse_forecasts(weather_payload, (POSITION,), NOW)[0]
    at_boundary = forecast_at(series, NOW)
    assert at_boundary.weather.rain_in_per_hr == pytest.approx(0.2)
    after_boundary = forecast_at(series, NOW + timedelta(seconds=1))
    assert after_boundary.weather.rain_in_per_hr == 0
    tie = forecast_at(series, NOW + timedelta(minutes=30))
    assert tie.wind_valid_at == NOW
    assert tie.precipitation_end == NOW + timedelta(hours=1)


def test_checkpoint_coverage_independent_of_missing_heatmap_hours(weather_payload):
    series = parse_forecasts(weather_payload, (POSITION,), NOW)[0]
    at_eta = forecast_at(series, NOW + timedelta(hours=1)).weather
    assert all(value is not None for value in at_eta.__dict__.values())
    beyond = forecast_at(series, NOW + timedelta(hours=48)).weather
    assert all(value is None for value in beyond.__dict__.values())
    assert forecast_at(series, NOW + timedelta(hours=1)).weather == at_eta


def test_hour_gap_does_not_get_filled(weather_payload):
    weather_payload["hourly"]["time"][1] += 1800
    series = parse_forecasts(weather_payload, (POSITION,), NOW)[0]
    result = forecast_at(series, NOW + timedelta(minutes=20))
    assert result.weather.rain_in_per_hr is None
