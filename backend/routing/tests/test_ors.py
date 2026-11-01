from copy import deepcopy
from datetime import UTC, datetime

import pytest

from routing.domain.types import Coordinate
from routing.providers.errors import ProviderError
from routing.providers.ors import OrsRouting, PeliasGeocoding, parse_routes, public_endpoint


@pytest.fixture
def ors_payload():
    """Synthetic geometry/timings; not a provider recording."""
    return {
        "type": "FeatureCollection",
        "metadata": {"query": {"profile": "driving-hgv"}},
        "features": [
            {
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-97, 32], [-96.99, 32], [-96.98, 32], [-96.97, 32]],
                },
                "properties": {
                    "summary": {"distance": 3000, "duration": 300},
                    "way_points": [0, 3],
                    "segments": [
                        {
                            "distance": 3000,
                            "duration": 300,
                            "steps": [
                                {"distance": 1000, "duration": 200, "way_points": [0, 1]},
                                {"distance": 2000, "duration": 100, "way_points": [1, 3]},
                                {"distance": 0, "duration": 0, "way_points": [3, 3]},
                            ],
                        }
                    ],
                    "warnings": [{"code": 1, "message": "Synthetic restriction"}],
                },
            }
        ],
    }


class SyntheticTransport:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post_json(self, provider, endpoint, body, headers):
        self.calls.append((provider, endpoint, body, headers))
        return self.payload

    def get_json(self, provider, endpoint, params, headers=None):
        self.calls.append((provider, endpoint, params, headers))
        return self.payload


def test_hgv_alternatives_steps_and_official_summary(ors_payload):
    transport = SyntheticTransport(ors_payload)
    result = OrsRouting("synthetic-test-key", transport=transport).discover(
        Coordinate(32, -97), Coordinate(32, -96.97), datetime.now(UTC)
    )
    _, endpoint, body, headers = transport.calls[0]
    assert endpoint.endswith("/driving-hgv/geojson")
    assert body["alternative_routes"]["target_count"] == 3
    assert body["coordinates"][0] == [-97, 32]
    assert "weight" not in body and "departure" not in body
    assert headers["Authorization"] == "synthetic-test-key"
    assert headers["Accept"] == "application/geo+json"
    route = result.routes[0]
    assert route.distance_m == 3000 and route.duration_s == 300
    assert route.sections[0].spans[1].end_offset == 3
    assert route.sections[0].spans[0].duration_s == 200
    assert route.notices[0].message == "Synthetic restriction"


def test_actual_counts_and_deduplication(ors_payload):
    ors_payload["features"].append(deepcopy(ors_payload["features"][0]))
    result = parse_routes(ors_payload)
    assert result.returned_count == 2 and len(result.routes) == 1 and result.duplicate_count == 1


@pytest.mark.parametrize(
    "invalid", [None, {}, {"type": "LineString"}, {"type": "FeatureCollection", "features": [None]}]
)
def test_invalid_ors_payload(invalid):
    with pytest.raises(ProviderError, match="invalid_payload"):
        parse_routes(invalid)


@pytest.mark.parametrize("field", ["profile", "coordinate", "step"])
def test_wrong_profile_and_coordinates_and_offsets(ors_payload, field):
    if field == "profile":
        ors_payload["metadata"]["query"]["profile"] = "driving-car"
    elif field == "coordinate":
        ors_payload["features"][0]["geometry"]["coordinates"][0] = [200, 90]
    else:
        ors_payload["features"][0]["properties"]["segments"][0]["steps"][0]["way_points"] = [0, 99]
    with pytest.raises(ProviderError):
        parse_routes(ors_payload)


def test_missing_credentials_fail_before_network():
    with pytest.raises(ProviderError, match="missing_credentials"):
        OrsRouting("").discover(Coordinate(32, -97), Coordinate(33, -97), datetime.now(UTC))


@pytest.mark.parametrize(
    "url", ["http://api.heigit.org", "https://paid.example", "https://api.heigit.org?token=x"]
)
def test_only_free_public_host_allowed(url):
    with pytest.raises(ValueError):
        public_endpoint(url)


def test_pelias_coordinate_order():
    transport = SyntheticTransport(
        {
            "features": [
                {
                    "geometry": {"coordinates": [-97, 32]},
                    "properties": {"gid": "synthetic:1", "label": "Synthetic place"},
                }
            ]
        }
    )
    places = PeliasGeocoding("synthetic-test-key", transport=transport).search("Synthetic")
    assert places[0]["position"] == [-97, 32]
    assert transport.calls[0][3]["Authorization"] == "synthetic-test-key"
