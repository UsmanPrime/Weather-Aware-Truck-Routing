"""HERE Routing v8 truck discovery; span metadata is not checkpoint timing proof."""

from datetime import UTC, datetime
from itertools import islice

import flexpolyline

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

ENDPOINT = "https://router.hereapi.com/v8/routes"


def parse_notices(values: list) -> tuple[Notice, ...]:
    return tuple(Notice(text(item["code"]), text(item["severity"])) for item in values)


def decode_geometry(encoded: str) -> tuple[Coordinate, ...]:
    if not isinstance(encoded, str) or not 1 <= len(encoded) <= 1_000_000:
        raise ValueError("Invalid encoded geometry size")
    try:
        decoded = tuple(islice(flexpolyline.iter_decode(encoded), 100_001))
    except RuntimeError:
        raise ValueError("Truncated flexible polyline") from None
    if not 2 <= len(decoded) <= 100_000 or any(len(point) != 2 for point in decoded):
        raise ValueError("Expected bounded 2D route geometry")
    return tuple(Coordinate(latitude=point[0], longitude=point[1]) for point in decoded)


def parse_section(section: dict) -> RouteSection:
    geometry = decode_geometry(section["polyline"])
    summary = section["summary"]
    travel = section["travelSummary"]
    if number(summary["length"]) <= 0 or number(summary["duration"]) <= 0:
        raise ValueError("Empty route section")
    spans = []
    for item in section.get("spans", []):
        offset = item["offset"]
        if type(offset) is not int or not 0 <= offset < len(geometry) - 1:
            raise ValueError("Invalid span offset")
        if (not spans and offset != 0) or (spans and offset <= spans[-1].offset):
            raise ValueError("Nonmonotonic span offsets")
        dynamic = item.get("dynamicSpeedInfo", {}).get("trafficSpeed")
        spans.append(
            RouteSpan(
                offset,
                number(item["length"]),
                number(item["duration"]),
                number(dynamic) if dynamic is not None else None,
                parse_notices(item.get("notices", [])),
            )
        )
    return RouteSection(
        text(section["id"]),
        geometry,
        number(summary["length"]),
        number(summary["duration"]),
        number(travel["duration"]),
        tuple(spans),
        parse_notices(section.get("notices", [])),
    )


def parse_routes(payload: object) -> RouteDiscovery:
    try:
        values = payload["routes"]
        if not isinstance(values, list) or len(values) > 3:
            raise ValueError("Invalid route count")
        routes, seen = [], set()
        duplicate_count = 0
        for item in values:
            if not isinstance(item["sections"], list) or not 1 <= len(item["sections"]) <= 100:
                raise ValueError("Invalid sections")
            sections = tuple(parse_section(section) for section in item["sections"])
            # Ignore redundant section joins when comparing alternative geometry.
            points = []
            for section in sections:
                for point in section.geometry:
                    if not points or point != points[-1]:
                        points.append(point)
            fingerprint = tuple(points)
            if fingerprint in seen:
                duplicate_count += 1
                continue
            seen.add(fingerprint)
            routes.append(
                ProviderRoute(text(item["id"]), sections, parse_notices(item.get("notices", [])))
            )
        return RouteDiscovery(tuple(routes), len(values), duplicate_count)
    except (KeyError, TypeError, ValueError, IndexError, OverflowError, AttributeError):
        raise invalid_payload("here") from None


class HereRouting:
    def __init__(self, api_key: str, transport: JsonTransport | None = None):
        self.api_key = api_key
        self.transport = transport or HttpTransport()

    def discover(
        self, origin: Coordinate, destination: Coordinate, departure_at: datetime
    ) -> RouteDiscovery:
        if not self.api_key:
            raise ProviderError(
                "here", "missing_credentials", "HERE_API_KEY is not configured.", 503
            )
        if departure_at.tzinfo is None or departure_at.utcoffset() is None:
            raise ValueError("Departure must be timezone-aware")
        if origin == destination:
            raise ValueError("Origin and destination must differ")
        params = {
            "apiKey": self.api_key,
            "transportMode": "truck",
            "routingMode": "fast",
            "alternatives": "2",
            "origin": f"{origin.latitude},{origin.longitude}",
            "destination": f"{destination.latitude},{destination.longitude}",
            "departureTime": departure_at.astimezone(UTC).isoformat(),
            "return": "polyline,summary,travelSummary",
            # Unlike duration/length, dynamicSpeedInfo induces speed-based span boundaries.
            "spans": "length,duration,dynamicSpeedInfo,notices",
        }
        return parse_routes(self.transport.get_json("here", ENDPOINT, params))
