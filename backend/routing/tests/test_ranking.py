from dataclasses import replace

import pytest

from routing.domain.ranking import RouteComparison, rank_routes

BASE = RouteComparison("base", 0, 0, 0, 3600)


@pytest.mark.parametrize(
    "preferred,other",
    [
        (
            replace(BASE, severe_m=1, high_m=99999, average_risk_index=3, duration_s=99999),
            replace(BASE, severe_m=2),
        ),
        (replace(BASE, high_m=1, average_risk_index=3, duration_s=99999), replace(BASE, high_m=2)),
        (
            replace(BASE, average_risk_index=1, duration_s=99999),
            replace(BASE, average_risk_index=2),
        ),
        (replace(BASE, duration_s=3599), BASE),
    ],
)
def test_exact_lexicographic_order(preferred, other):
    assert rank_routes([other, preferred]) == (preferred, other)


def test_ineligible_routes_never_beat_eligible_routes():
    unsafe = replace(BASE, route_id="unsafe", no_travel_m=0.001)
    unknown = replace(BASE, route_id="unknown", complete=False)
    no_average = replace(BASE, route_id="missing-average", average_risk_index=None)
    assert rank_routes([unsafe, unknown, no_average, BASE]) == (BASE,)
    assert rank_routes([unsafe, unknown]) == ()
    assert rank_routes([]) == ()


def test_exact_ties_keep_provider_order():
    other = replace(BASE, route_id="other")
    assert rank_routes([other, BASE]) == (other, BASE)


@pytest.mark.parametrize(
    "changes",
    [
        {"severe_m": -1},
        {"high_m": float("nan")},
        {"duration_s": float("inf")},
        {"average_risk_index": -1},
        {"average_risk_index": 4.1},
        {"no_travel_m": -1},
    ],
)
def test_invalid_metrics_rejected(changes):
    with pytest.raises(ValueError):
        replace(BASE, **changes)
