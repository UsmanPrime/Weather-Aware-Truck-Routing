"""Free HeiGIT driving-hgv GeoJSON. Keys travel only in Authorization headers."""

from datetime import datetime
from hashlib import sha256
from urllib.parse import urlsplit

from routing.domain.types import (
    Coordinate,
    Notice,
    ProviderRoute,
    RouteDiscovery,
    RouteSection,
    RouteSpan,
)

from .errors import ProviderError, invalid_payload
from .http import HttpTransport, JsonTransport
from .validation import number, text

DEFAULT_BASE = "https://api.heigit.org/openrouteservice"
DEFAULT_GEOCODING = "https://api.heigit.org/pelias/v1"


def public_endpoint(base: str) -> str:
    parsed = urlsplit(base)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "api.heigit.org"
        or (parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.port)
    ):
        raise ValueError("Only the free HTTPS HeiGIT service is supported")
    return base.rstrip("/")


def warnings(values: list) -> tuple[Notice, ...]:
    return tuple(Notice(str(item["code"]), "warning", text(item["message"])) for item in values)


def parse_routes(payload: object) -> RouteDiscovery:
    try:
        if payload["type"] != "FeatureCollection":
            raise ValueError("Expected route FeatureCollection")
        features = payload["features"]
        if not isinstance(features, list) or len(features) > 3:
            raise ValueError("Unexpected route count")
        profile = payload.get("metadata", {}).get("query", {}).get("profile")
        if profile is not None and profile != "driving-hgv":
            raise ValueError("Incorrect truck profile")
        result, seen, duplicates = [], set(), 0
        for feature in features:
            geometry, props = feature["geometry"], feature["properties"]
            if geometry["type"] != "LineString" or not 2 <= len(geometry["coordinates"]) <= 100_000:
                raise ValueError("Invalid road geometry")
            points = tuple(
                Coordinate(latitude=p[1], longitude=p[0]) for p in geometry["coordinates"]
            )
            fingerprint = tuple(
                dict.fromkeys((round(p.latitude, 6), round(p.longitude, 6)) for p in points)
            )
            if fingerprint in seen:
                duplicates += 1
                continue
            seen.add(fingerprint)
            route_id = "ors-" + sha256(repr(fingerprint).encode()).hexdigest()[:12]
            distance, duration = (
                number(props["summary"]["distance"]),
                number(props["summary"]["duration"]),
            )
            if distance <= 0 or duration <= 0:
                raise ValueError("Empty route")
            segments = props.get("segments", [])
            waypoints = props.get("way_points", [0, len(points) - 1])
            sections = []
            if segments and len(waypoints) != len(segments) + 1:
                raise ValueError("Mismatched sections")
            for index, segment in enumerate(segments):
                start, end = waypoints[index : index + 2]
                if (
                    type(start) is not int
                    or type(end) is not int
                    or not 0 <= start < end < len(points)
                ):
                    raise ValueError("Invalid section offsets")
                spans = []
                for step in segment.get("steps", []):
                    left, right = step["way_points"]
                    length, seconds = number(step["distance"]), number(step["duration"])
                    if (
                        type(left) is not int
                        or type(right) is not int
                        or not start <= left <= right <= end
                    ):
                        raise ValueError("Invalid step offsets")
                    if left == right:
                        if length or seconds:
                            raise ValueError("Nonempty step without geometry")
                        continue  # zero-distance arrival instruction
                    spans.append(
                        RouteSpan(left - start, length, seconds, None, end_offset=right - start)
                    )
                sections.append(
                    RouteSection(
                        f"{route_id}-section-{index}",
                        points[start : end + 1],
                        number(segment["distance"]),
                        number(segment["duration"]),
                        number(segment["duration"]),
                        tuple(spans),
                        (),
                    )
                )
            if not sections:
                sections.append(
                    RouteSection(
                        route_id + "-section-0", points, distance, duration, duration, (), ()
                    )
                )
            result.append(
                ProviderRoute(
                    route_id,
                    tuple(sections),
                    warnings(props.get("warnings", [])),
                    "ors",
                    distance,
                    duration,
                )
            )
        return RouteDiscovery(tuple(result), len(features), duplicates)
    except (KeyError, TypeError, ValueError, IndexError, OverflowError, AttributeError):
        raise invalid_payload("ors") from None


class OrsRouting:
    def __init__(
        self, api_key: str, base_url: str = DEFAULT_BASE, transport: JsonTransport | None = None
    ):
        self.api_key = api_key
        self.base_url = public_endpoint(base_url)
        self.transport = transport or HttpTransport(timeout_s=12)

    def discover(
        self, origin: Coordinate, destination: Coordinate, departure_at: datetime
    ) -> RouteDiscovery:
        if not self.api_key:
            raise ProviderError("ors", "missing_credentials", "ORS_API_KEY is not configured.", 503)
        if departure_at.tzinfo is None or departure_at.utcoffset() is None:
            raise ValueError("Departure must be timezone-aware")
        if origin == destination:
            raise ValueError("Origin and destination must differ")
        body = {
            "coordinates": [
                [origin.longitude, origin.latitude],
                [destination.longitude, destination.latitude],
            ],
            "units": "m",
            "instructions": True,
            "alternative_routes": {"target_count": 3, "share_factor": 0.8, "weight_factor": 1.6},
        }
        payload = self.transport.post_json(
            "ors",
            self.base_url + "/v2/directions/driving-hgv/geojson",
            body,
            {"Authorization": self.api_key, "Accept": "application/geo+json"},
        )
        return parse_routes(payload)


class PeliasGeocoding:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_GEOCODING,
        transport: JsonTransport | None = None,
    ):
        self.api_key = api_key
        self.base_url = public_endpoint(base_url)
        self.transport = transport or HttpTransport()

    def search(self, query: str) -> list[dict]:
        if not self.api_key:
            raise ProviderError(
                "pelias", "missing_credentials", "ORS_API_KEY is not configured.", 503
            )
        payload = self.transport.get_json(
            "pelias",
            self.base_url + "/search",
            {"text": query, "size": "5", "boundary.country": "USA"},
            headers={"Authorization": self.api_key},
        )
        try:
            result = []
            for feature in payload["features"][:5]:
                coords, props = feature["geometry"]["coordinates"], feature["properties"]
                position = Coordinate(latitude=coords[1], longitude=coords[0])
                result.append(
                    {
                        "id": text(props["gid"]),
                        "label": text(props["label"]),
                        "position": [position.longitude, position.latitude],
                    }
                )
            return result
        except (KeyError, TypeError, ValueError, IndexError, OverflowError):
            raise invalid_payload("pelias") from None
