from copy import deepcopy
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from django.core.signing import TimestampSigner
from rest_framework.test import APIClient

from routing.domain.corridor import corridor_grid
from routing.providers.errors import ProviderError
from routing.services.context import MAX_JSON, SALT, create_context, read_context
from routing.services.corridor import corridor_forecast
from routing.services.planning import plan_trip
from routing.tests.test_pipeline import Forecasts, Routes, request_data


def context():
    return create_context(
        [{"geometry": {"coordinates": [[-97.3308, 32.7555], [-96.797, 32.7767]]}}],
        datetime.now(UTC).isoformat(),
        30000,
    )


def test_signed_context_roundtrip_and_tampering():
    token = context()
    assert read_context(token)["load_lb"] == 30000
    with pytest.raises(ProviderError, match="invalid_context"):
        read_context(token + "tampered")


def test_expired_context_rejected():
    import time

    token = context()
    with patch("django.core.signing.time.time", return_value=time.time() + 1801):
        with pytest.raises(ProviderError, match="expired_context") as caught:
            read_context(token)
    assert caught.value.http_status == 410


@pytest.mark.parametrize(
    "variant", ["compressed", "oversize", "points", "coordinate", "load", "naive"]
)
def test_signed_but_invalid_payload_limits(variant):
    payload = read_context(context())
    if variant == "oversize":
        payload["extra"] = "x" * (MAX_JSON + 1)
    elif variant == "points":
        payload["routes"] = [payload["routes"][0] * 3001]
    elif variant == "coordinate":
        payload["routes"][0][0][0] = 181
    elif variant == "load":
        payload["load_lb"] = float("nan")
    elif variant == "naive":
        payload["departure_at"] = "2026-11-01T12:00:00"
    token = TimestampSigner(salt=SALT).sign_object(payload, compress=variant == "compressed")
    with pytest.raises(ProviderError, match="invalid_context"):
        read_context(token)


def test_corridor_is_bounded_and_covers_all_alternatives():
    routes = [[[-97, 32], [-96.5, 32]], [[-97, 33], [-96.5, 33]]]
    cells, spacing, width = corridor_grid(routes)
    assert 0 < len(cells) <= 96 and spacing >= 12000 and width == 25000
    assert any(c["position"][1] < 32.2 for c in cells)
    assert any(c["position"][1] > 32.8 for c in cells)
    assert not any(32.3 < c["position"][1] < 32.7 for c in cells)
    assert all(c["polygon"][0] == c["polygon"][-1] and len(c["polygon"]) == 5 for c in cells)


def test_heatmap_has_49_frames_and_does_not_change_plan_risk():
    data = request_data()
    plan = plan_trip(data, routes_provider=Routes(), forecasts_provider=Forecasts())
    before = deepcopy(plan)
    result = corridor_forecast(plan["corridor_context"], forecasts_provider=Forecasts())
    assert len(result["frames"]) == 49
    assert result["frames"][0]["coverage_fraction"] == 1
    assert result["frames"][-1]["coverage_fraction"] == 0
    assert all(r is None for r in result["frames"][-1]["risk"])
    assert 48 in result["frames_with_missing_data"]
    assert plan == before
    assert plan["routes"][0]["status"] == "complete"
    assert all(len(f["risk"]) == len(result["cells"]) for f in result["frames"])


@pytest.mark.parametrize("routes", [[[[179, 30], [-179, 30]]], [[[0, 80], [1, 81]]]])
def test_unsupported_grid_geography_is_explicit(routes):
    with pytest.raises(ValueError):
        corridor_grid(routes)


def test_corridor_request_validation_and_body_limit():
    client = APIClient()
    assert client.post("/api/v1/corridor-forecasts", [], format="json").status_code == 400
    assert (
        client.post("/api/v1/corridor-forecasts", {"context": "invalid"}, format="json").status_code
        == 400
    )
    response = client.post(
        "/api/v1/corridor-forecasts",
        '{"context":"' + "a" * 300000 + '"}',
        content_type="application/json",
    )
    assert response.status_code == 413
    assert response.json()["error"]["request_id"]
