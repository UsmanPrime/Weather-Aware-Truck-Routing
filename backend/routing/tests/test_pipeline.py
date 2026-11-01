"""Synthetic complete pipeline tests; network-free and independent of live model output."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from routing.domain.exposure import aggregate_exposure
from routing.domain.geometry import distance, route_edges, sample_route
from routing.domain.risk import assess_weather
from routing.domain.types import (
    Coordinate,
    ForecastSeries,
    HourlyForecast,
    ProviderRoute,
    RouteDiscovery,
    RouteSection,
    RouteSpan,
    Weather,
)
from routing.domain.units import miles_to_meters
from routing.providers.errors import ProviderError
from routing.services.planning import plan_trip

NOW = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def road(length=100000, seconds=4000):
    coordinates = (Coordinate(32, -97), Coordinate(32, -96.5), Coordinate(32, -96))
    spans = (
        RouteSpan(0, length / 2, seconds * 0.8, None, end_offset=1),
        RouteSpan(1, length / 2, seconds * 0.2, None, end_offset=2),
    )
    return ProviderRoute(
        "synthetic-route",
        (RouteSection("s", coordinates, length, seconds, seconds, spans, ()),),
        (),
        "ors",
    )


class Routes:
    def __init__(self, routes=None):
        self.routes = routes or [replace(road(), id=f"synthetic-{i}") for i in range(3)]

    def discover(self, *args):
        return RouteDiscovery(tuple(self.routes), len(self.routes), 0)


class Forecasts:
    def __init__(self, weather=None):
        self.weather = weather if weather is not None else Weather(10, 0, 0)

    def forecast(self, positions):
        return tuple(
            ForecastSeries(
                p,
                p,
                NOW,
                tuple(
                    HourlyForecast(
                        NOW + timedelta(hours=i),
                        NOW + timedelta(hours=i - 1),
                        NOW + timedelta(hours=i),
                        self.weather,
                    )
                    for i in range(6)
                ),
            )
            for p in positions
        )


def request_data():
    return {
        "origin": {"id": "a", "label": "Synthetic origin", "position": [-97, 32]},
        "destination": {"id": "b", "label": "Synthetic destination", "position": [-96, 32]},
        "departure_at": NOW,
        "departure_timezone": "America/Chicago",
        "load_lb": 30000,
        "checkpoint_interval_mi": 25,
    }


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()


@pytest.mark.parametrize("interval", [10, 25, 50])
@pytest.mark.parametrize("multiple,remainder", [(0, 100), (1, 0), (2, 0), (2, 10)])
def test_checkpoint_spacing_and_exact_endpoints(interval, multiple, remainder):
    length = miles_to_meters(interval) * multiple + remainder
    samples, _ = sample_route(road(length), interval)
    chainages = [p.distance_m for p in samples]
    assert chainages[0] == 0 and chainages[-1] == length
    assert len(chainages) == len(set(chainages))
    assert sum(b - a for a, b in zip(chainages[:-1], chainages[1:], strict=True)) == pytest.approx(
        length
    )
    assert all(
        b - a == pytest.approx(miles_to_meters(interval))
        for a, b in zip(chainages[:-2], chainages[1:-1], strict=True)
    )
    assert samples[0].position == road().sections[0].geometry[0]
    assert samples[-1].position == road().sections[0].geometry[-1]
    assert samples[-1].elapsed_s == pytest.approx(4000)


def test_nonuniform_step_time_and_midnight():
    edges, notes = route_edges(road())
    assert not notes
    assert edges[0].end_m == pytest.approx(50000)
    assert edges[0].end_s == pytest.approx(3200)
    data = request_data()
    data["departure_at"] = NOW.replace(hour=23, minute=50)
    result = plan_trip(data, routes_provider=Routes(), forecasts_provider=Forecasts())
    assert result["routes"][0]["arrival_at"].startswith(
        (data["departure_at"] + timedelta(days=1)).date().isoformat()
    )


def test_multiple_sections_and_missing_timing_fallback():
    original = road()
    first = replace(
        original.sections[0],
        geometry=original.sections[0].geometry[:2],
        distance_m=50000,
        duration_s=1000,
        travel_duration_s=1000,
        spans=(),
    )
    second = replace(first, id="s2", geometry=original.sections[0].geometry[1:], duration_s=3000)
    route = replace(original, sections=(first, second))
    edges, notes = route_edges(route)
    assert notes and edges[0].end_s == pytest.approx(1000)
    assert edges[-1].end_m == 100000 and edges[-1].end_s == 4000


def test_disconnected_and_degenerate_geometry_rejected():
    original = road()
    with pytest.raises(ValueError):
        route_edges(replace(original, sections=original.sections + (original.sections[0],)))
    section = replace(original.sections[0], geometry=(Coordinate(0, 0), Coordinate(0, 0)), spans=())
    with pytest.raises(ValueError):
        route_edges(replace(original, sections=(section,)))


def test_exposure_is_miles_not_checkpoint_count():
    low = assess_weather(Weather(0, 0, 0), 0)
    severe = assess_weather(Weather(45, 0, 0), 0)
    high = assess_weather(Weather(35, 0, 0), 0)
    exposure = aggregate_exposure([0, 10, 90, 100], [low, severe, low, high])
    assert exposure.risk_distance_m["severe"] == 90
    assert exposure.risk_distance_m["high"] == 10
    assert exposure.average_risk_index == 2.9
    assert exposure.coverage_fraction == 1


def test_unknown_and_no_travel_preserved_together():
    unknown = assess_weather(Weather(None, None, None), 0)
    unsafe = assess_weather(Weather(55, None, None), 0)
    exposure = aggregate_exposure([0, 100], [unknown, unsafe])
    assert exposure.status == "no_travel"
    assert exposure.risk_distance_m["no_travel"] == 100
    assert exposure.coverage_fraction == 0 and exposure.average_risk_index is None


@pytest.mark.parametrize(
    "weather,status,state",
    [
        (Weather(0, 0, 0), "complete", "recommended"),
        (Weather(55, 0, 0), "no_travel", "no_safe_route"),
        (Weather(None, 0, 0), "incomplete", "incomplete"),
    ],
)
def test_complete_pipeline_statuses(weather, status, state):
    result = plan_trip(
        request_data(), routes_provider=Routes(), forecasts_provider=Forecasts(weather)
    )
    assert result["actual_route_count"] == 3
    assert result["recommendation"]["state"] == state
    for route in result["routes"]:
        assert route["status"] == status
        assert sum(route["risk_distance_m"].values()) + route[
            "unknown_distance_m"
        ] == pytest.approx(route["distance_m"])
        assert route["checkpoints"][0]["weather"]["source"] == "open_meteo"
        assert route["checkpoints"][-1]["eta"] == route["arrival_at"]


def test_provider_weather_failure_produces_unknown_routes():
    class Failure:
        def forecast(self, *args):
            raise ProviderError("open_meteo", "timeout", "Timed out.", 504, True)

    result = plan_trip(request_data(), routes_provider=Routes(), forecasts_provider=Failure())
    assert result["recommendation"]["route_id"] is None
    assert result["routes"][0]["unknown_distance_m"] == 100000
    assert result["warnings"][0]["code"] == "timeout"


def test_fewer_routes_is_provisional_and_no_routes_fails():
    result = plan_trip(
        request_data(), routes_provider=Routes([road()]), forecasts_provider=Forecasts()
    )
    assert result["recommendation"]["scope"] == "available_candidates"

    class Empty:
        def discover(self, *args):
            return RouteDiscovery((), 0, 0)

    with pytest.raises(ProviderError):
        plan_trip(request_data(), routes_provider=Empty())


def test_api_pipeline_and_response_contract():
    data = request_data()
    data["departure_at"] = NOW.isoformat()
    with (
        patch("routing.services.planning.routing_provider", return_value=Routes()),
        patch("routing.services.forecasts.OpenMeteo", return_value=Forecasts()),
    ):
        response = APIClient().post("/api/v1/plans", data, format="json")
    assert response.status_code == 200, response.data
    assert response.json()["schema_version"] == "1"
    assert response.json()["recommendation"]["route_id"] == "synthetic-0"


@pytest.mark.parametrize(
    "changes",
    [
        {"load_lb": -1},
        {"load_lb": "NaN"},
        {"checkpoint_interval_mi": 12},
        {"departure_at": "2026-11-01T12:00:00"},
        {"departure_timezone": "Invalid/Zone"},
        {"origin": {"id": "a", "label": "Invalid", "position": [190, 20]}},
    ],
)
def test_invalid_requests_are_structured(changes):
    data = request_data()
    data["departure_at"] = NOW.isoformat()
    data.update(changes)
    response = APIClient().post("/api/v1/plans", data, format="json")
    assert response.status_code == 400
    assert response.json()["error"]["request_id"]


def test_geocode_contract_and_validation():
    with patch("routing.api.views.PeliasGeocoding") as adapter:
        adapter.return_value.search.return_value = [
            {"id": "a", "label": "Synthetic", "position": [-97, 32]}
        ]
        response = APIClient().get("/api/v1/geocode", {"q": "Fort Worth"})
    assert response.status_code == 200 and len(response.json()["places"]) == 1
    assert APIClient().get("/api/v1/geocode", {"q": "a"}).status_code == 400


def test_geodesic_is_not_route_distance():
    assert distance(Coordinate(0, 0), Coordinate(0, 1)) == pytest.approx(111195, rel=0.001)
    assert road().distance_m != distance(*[road().sections[0].geometry[i] for i in (0, -1)])


def test_pipeline_uses_arrival_weather_not_departure_weather():
    class ChangingForecast:
        def forecast(self, positions):
            series = Forecasts().forecast(positions)
            return tuple(
                replace(
                    s,
                    hours=tuple(
                        replace(h, weather=Weather(55 if i else 0, 0, 0))
                        for i, h in enumerate(s.hours)
                    ),
                )
                for s in series
            )

    result = plan_trip(
        request_data(), routes_provider=Routes(), forecasts_provider=ChangingForecast()
    )
    route = result["routes"][0]
    assert route["checkpoints"][0]["risk"] == "low"
    assert route["checkpoints"][-1]["risk"] == "no_travel"
    assert route["risk_distance_m"]["no_travel"] > 0
    assert result["recommendation"]["route_id"] is None


def test_plan_rate_limit_is_structured():
    client = APIClient()
    responses = [client.post("/api/v1/plans", {}, format="json") for _ in range(6)]
    assert responses[-1].status_code == 429
    assert responses[-1].json()["error"]["retryable"] is True


def test_forecast_exact_coordinate_cache_reuse():
    from routing.services.forecasts import load_forecasts

    provider = Forecasts()
    with patch("routing.services.forecasts.OpenMeteo", return_value=provider) as factory:
        positions = (Coordinate(32, -97), Coordinate(32, -96.99))
        one, _ = load_forecasts(positions)
        two, _ = load_forecasts(tuple(reversed(positions)))
        assert factory.call_count == 1
        assert one == two
