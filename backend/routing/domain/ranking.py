"""Lexicographic PDF preferences, not a weighted risk/time score."""

from dataclasses import dataclass

from .units import nonnegative


@dataclass(frozen=True)
class RouteComparison:
    route_id: str
    severe_m: float
    high_m: float
    average_risk_index: float | None
    duration_s: float
    no_travel_m: float = 0
    complete: bool = True

    def __post_init__(self):
        values = (self.severe_m, self.high_m, self.duration_s, self.no_travel_m)
        if not self.route_id or any(nonnegative(value) is None for value in values):
            raise ValueError("Invalid route comparison")
        if self.average_risk_index is not None and (
            nonnegative(self.average_risk_index) is None or self.average_risk_index > 4
        ):
            raise ValueError("Average risk index must be between zero and four")

    @property
    def eligible(self) -> bool:
        return self.complete and self.no_travel_m == 0 and self.average_risk_index is not None


def rank_routes(routes: list[RouteComparison]) -> tuple[RouteComparison, ...]:
    """Stable input order breaks exact ties; caller must disclose excluded candidates."""
    return tuple(
        sorted(
            (route for route in routes if route.eligible),
            key=lambda route: (
                route.severe_m,
                route.high_m,
                route.average_risk_index,
                route.duration_s,
            ),
        )
    )
