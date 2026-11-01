"""Road chainage and time mapping using official totals, not endpoint distance."""

from bisect import bisect_left
from dataclasses import dataclass
from math import asin, atan2, cos, degrees, radians, sin, sqrt

from .types import Coordinate, ProviderRoute, RouteSpan
from .units import miles_to_meters

EARTH_RADIUS_M = 6_371_008.8


def distance(a: Coordinate, b: Coordinate) -> float:
    lat1, lat2 = radians(a.latitude), radians(b.latitude)
    dlat, dlon = lat2 - lat1, radians(b.longitude - a.longitude)
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(min(1, max(0, h))))


def interpolate(a: Coordinate, b: Coordinate, fraction: float) -> Coordinate:
    if fraction <= 0:
        return a
    if fraction >= 1:
        return b
    # Great-circle interpolation; handles antimeridian without crossing the map the wrong way.
    angle = distance(a, b) / EARTH_RADIUS_M
    if angle < 1e-12:
        return a
    p, q = sin((1 - fraction) * angle) / sin(angle), sin(fraction * angle) / sin(angle)
    lat1, lon1, lat2, lon2 = map(radians, (a.latitude, a.longitude, b.latitude, b.longitude))
    x = p * cos(lat1) * cos(lon1) + q * cos(lat2) * cos(lon2)
    y = p * cos(lat1) * sin(lon1) + q * cos(lat2) * sin(lon2)
    z = p * sin(lat1) + q * sin(lat2)
    return Coordinate(degrees(atan2(z, sqrt(x * x + y * y))), degrees(atan2(y, x)))


@dataclass(frozen=True)
class TimedEdge:
    start: Coordinate
    end: Coordinate
    start_m: float
    end_m: float
    start_s: float
    end_s: float


@dataclass(frozen=True)
class Sample:
    position: Coordinate
    distance_m: float
    elapsed_s: float


def route_edges(route: ProviderRoute) -> tuple[tuple[TimedEdge, ...], tuple[str, ...]]:
    section_m = sum(s.distance_m for s in route.sections)
    section_s = sum(s.duration_s for s in route.sections)
    if route.distance_m <= 0 or route.duration_s <= 0 or section_m <= 0 or section_s <= 0:
        raise ValueError("Route has no positive distance/duration")
    edges, warnings = [], []
    current_m = current_s = 0.0
    previous = None
    for section in route.sections:
        if section.distance_m <= 0 or section.duration_s <= 0:
            raise ValueError("Empty road section")
        if previous and distance(previous, section.geometry[0]) > 25:
            raise ValueError("Disconnected route sections")
        previous = section.geometry[-1]
        spans = section.spans
        good = bool(spans) and spans[0].offset == 0
        for index, span in enumerate(spans):
            end = (
                span.end_offset
                if span.end_offset is not None
                else (
                    spans[index + 1].offset if index + 1 < len(spans) else len(section.geometry) - 1
                )
            )
            expected_end = (
                spans[index + 1].offset if index + 1 < len(spans) else len(section.geometry) - 1
            )
            good = good and end == expected_end and span.offset < end and span.length_m > 0
        total_m, total_s = sum(s.length_m for s in spans), sum(s.duration_s for s in spans)
        good = (
            good
            and total_m > 0
            and total_s > 0
            and (
                abs(total_m - section.distance_m) <= max(2, section.distance_m * 0.01)
                and abs(total_s - section.duration_s) <= max(2, section.duration_s * 0.01)
            )
        )
        if not good:
            spans = (
                RouteSpan(
                    0,
                    section.distance_m,
                    section.duration_s,
                    None,
                    end_offset=len(section.geometry) - 1,
                ),
            )
            total_m, total_s = section.distance_m, section.duration_s
            warnings.append(
                "Section-level time approximation: complete instruction timing unavailable."
            )
        for index, span in enumerate(spans):
            end = (
                span.end_offset
                if span.end_offset is not None
                else (
                    spans[index + 1].offset if index + 1 < len(spans) else len(section.geometry) - 1
                )
            )
            coordinates = section.geometry[span.offset : end + 1]
            lengths = [
                distance(a, b) for a, b in zip(coordinates[:-1], coordinates[1:], strict=True)
            ]
            geometric_total = sum(lengths)
            if geometric_total <= 0:
                raise ValueError("Degenerate road geometry")
            span_m = span.length_m / total_m * section.distance_m * route.distance_m / section_m
            span_s = span.duration_s / total_s * section.duration_s * route.duration_s / section_s
            for a, b, length in zip(coordinates[:-1], coordinates[1:], lengths, strict=True):
                if length == 0:
                    continue
                next_m = current_m + span_m * length / geometric_total
                next_s = current_s + span_s * length / geometric_total
                edges.append(TimedEdge(a, b, current_m, next_m, current_s, next_s))
                current_m, current_s = next_m, next_s
    if not edges:
        raise ValueError("No traversable road geometry")
    last = edges[-1]
    edges[-1] = TimedEdge(
        last.start, last.end, last.start_m, route.distance_m, last.start_s, route.duration_s
    )
    return tuple(edges), tuple(dict.fromkeys(warnings))


def sample_route(
    route: ProviderRoute, interval_mi: int
) -> tuple[tuple[Sample, ...], tuple[str, ...]]:
    if interval_mi not in (10, 25, 50):
        raise ValueError("Interval must be 10, 25 or 50 miles")
    edges, warnings = route_edges(route)
    spacing = miles_to_meters(interval_mi)
    positions = [0.0]
    next_m = spacing
    while next_m < route.distance_m - 1e-6:
        positions.append(next_m)
        next_m += spacing
        if len(positions) > 600:
            raise ValueError("Trip exceeds checkpoint limit; choose coarser spacing")
    positions.append(route.distance_m)
    ends = [e.end_m for e in edges]
    result = []
    for chainage in positions:
        edge = edges[min(bisect_left(ends, chainage), len(edges) - 1)]
        fraction = max(0, min(1, (chainage - edge.start_m) / (edge.end_m - edge.start_m)))
        result.append(
            Sample(
                interpolate(edge.start, edge.end, fraction),
                chainage,
                edge.start_s + fraction * (edge.end_s - edge.start_s),
            )
        )
    return tuple(result), warnings


def joined_geometry(route: ProviderRoute) -> list[list[float]]:
    result = []
    for section in route.sections:
        for point in section.geometry:
            coordinate = [point.longitude, point.latitude]
            if not result or result[-1] != coordinate:
                result.append(coordinate)
    return result
