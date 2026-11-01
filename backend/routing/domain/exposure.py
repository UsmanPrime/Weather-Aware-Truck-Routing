from dataclasses import dataclass
from math import isfinite

from .risk import RiskAssessment
from .types import Risk


@dataclass(frozen=True)
class Exposure:
    risk_distance_m: dict[str, float]
    unknown_distance_m: float
    coverage_fraction: float
    average_risk_index: float | None
    segments: tuple[dict, ...]
    status: str


def aggregate_exposure(chainages: list[float], assessments: list[RiskAssessment]) -> Exposure:
    if any(not isfinite(value) for value in chainages):
        raise ValueError("Chainages must be finite")
    if len(chainages) != len(assessments) or len(chainages) < 2 or chainages[0] != 0:
        raise ValueError("Exposure requires matching ordered checkpoints starting at zero")
    totals = {risk.name.lower(): 0.0 for risk in Risk}
    unknown = covered = weighted = 0.0
    segments = []
    for i in range(len(chainages) - 1):
        length = chainages[i + 1] - chainages[i]
        if length <= 0:
            raise ValueError("Checkpoint chainages must increase")
        a, b = assessments[i : i + 2]
        severity = (
            Risk.NO_TRAVEL
            if Risk.NO_TRAVEL in (a.risk, b.risk)
            else None
            if a.risk is None or b.risk is None
            else max(a.risk, b.risk)
        )
        if not a.missing_fields and not b.missing_fields:
            covered += length
        if severity is None:
            unknown += length
        else:
            totals[severity.name.lower()] += length
            weighted += length * int(severity)
        segments.append(
            {
                "from_index": i,
                "to_index": i + 1,
                "distance_m": length,
                "risk": severity.name.lower() if severity is not None else None,
            }
        )
    complete = all(not a.missing_fields and a.risk is not None for a in assessments)
    status = "no_travel" if totals["no_travel"] > 0 else "complete" if complete else "incomplete"
    return Exposure(
        totals,
        unknown,
        covered / chainages[-1],
        weighted / chainages[-1] if complete else None,
        tuple(segments),
        status,
    )
