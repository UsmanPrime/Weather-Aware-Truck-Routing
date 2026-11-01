import os
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from time import monotonic
from uuid import uuid4

from routing.domain.exposure import aggregate_exposure
from routing.domain.forecast import forecast_at
from routing.domain.geometry import joined_geometry, sample_route
from routing.domain.ranking import RouteComparison, rank_routes
from routing.domain.risk import assess_weather
from routing.domain.types import Coordinate, Weather
from routing.providers.errors import ProviderError
from routing.providers.factory import routing_provider

from .cache import cached_call
from .context import create_context
from .forecasts import load_forecasts


def instant(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def plan_trip(data: dict, *, routes_provider=None, forecasts_provider=None) -> dict:
    deadline = monotonic() + 20
    origin = Coordinate(data["origin"]["position"][1], data["origin"]["position"][0])
    destination = Coordinate(data["destination"]["position"][1], data["destination"]["position"][0])
    provider = routes_provider or routing_provider()
    discovery = (
        provider.discover(origin, destination, data["departure_at"])
        if routes_provider
        else cached_call(
            "routes",
            (
                os.environ.get("ROUTING_PROVIDER", "ors"),
                origin,
                destination,
                data["departure_at"] if os.environ.get("ROUTING_PROVIDER") == "here" else None,
            ),
            300,
            lambda: provider.discover(origin, destination, data["departure_at"]),
            "ors",
        )
    )
    if not discovery.routes:
        raise ProviderError(
            "ors", "no_routes", "No truck route was returned for these locations.", 422
        )
    warnings, sampled = [], []
    for route in discovery.routes:
        try:
            samples, notes = sample_route(route, data["checkpoint_interval_mi"])
            sampled.append((route, samples, notes))
        except ValueError as error:
            if "checkpoint limit" in str(error):
                raise ProviderError(
                    "ors", "trip_limit", "Too many checkpoints; choose coarser spacing.", 422
                ) from None
            warnings.append(
                {
                    "code": "unusable_geometry",
                    "message": "A route could not be sampled reliably.",
                    "route_id": route.id,
                }
            )
    if not sampled:
        raise ProviderError(
            "ors", "unusable_routes", "Provider routes could not be evaluated.", 502
        )
    all_positions = tuple(sample.position for _, samples, _ in sampled for sample in samples)
    if len(all_positions) > 600:
        raise ProviderError(
            "ors", "trip_limit", "Too many checkpoints; choose coarser spacing.", 422
        )
    forecasts, weather_warnings = load_forecasts(
        all_positions, provider=forecasts_provider, deadline=deadline
    )
    warnings.extend(weather_warnings)
    routes, comparisons = [], []
    for index, (route, samples, notes) in enumerate(sampled):
        checkpoints, assessments = [], []
        for i, sample in enumerate(samples):
            eta = data["departure_at"] + timedelta(seconds=sample.elapsed_s)
            series = forecasts.get(sample.position)
            selected = forecast_at(series, eta) if series else None
            weather = selected.weather if selected else Weather(None, None, None)
            assessment = assess_weather(weather, data["load_lb"])
            assessments.append(assessment)
            checkpoints.append(
                {
                    "id": f"{route.id}-cp-{i}",
                    "position": [sample.position.longitude, sample.position.latitude],
                    "distance_from_start_m": sample.distance_m,
                    "eta": instant(eta),
                    "risk": assessment.risk.name.lower() if assessment.risk is not None else None,
                    "hazards": {
                        key: getattr(assessment, key).name.lower()
                        if getattr(assessment, key) is not None
                        else None
                        for key in ("wind", "rain", "snow")
                    },
                    "missing_fields": list(assessment.missing_fields),
                    "weather": {
                        **asdict(weather),
                        "source": "open_meteo",
                        "data_kind": "forecast",
                        "retrieved_at": instant(series.retrieved_at) if series else None,
                        "wind_valid_at": instant(selected.wind_valid_at)
                        if selected and selected.wind_valid_at
                        else None,
                        "precipitation_interval_start": instant(selected.precipitation_start)
                        if selected and selected.precipitation_start
                        else None,
                        "precipitation_interval_end": instant(selected.precipitation_end)
                        if selected and selected.precipitation_end
                        else None,
                    },
                }
            )
        exposure = aggregate_exposure([s.distance_m for s in samples], assessments)
        eligible = exposure.status == "complete"
        comparisons.append(
            RouteComparison(
                route.id,
                exposure.risk_distance_m["severe"],
                exposure.risk_distance_m["high"],
                exposure.average_risk_index,
                route.duration_s,
                exposure.risk_distance_m["no_travel"],
                exposure.status != "incomplete",
            )
        )
        routes.append(
            {
                "id": route.id,
                "label": f"Route {index + 1}",
                "geometry": {"type": "LineString", "coordinates": joined_geometry(route)},
                "distance_m": route.distance_m,
                "duration_s": route.duration_s,
                "arrival_at": instant(data["departure_at"] + timedelta(seconds=route.duration_s)),
                "checkpoints": checkpoints,
                **asdict(exposure),
                "eligible": eligible,
                "provider": route.provider,
                "provider_notices": [asdict(n) for n in route.notices],
                "timing_method": "section_distance_approximation"
                if notes
                else "instruction_step_interpolation",
                "timing_notes": list(notes)
                or ["Estimated within instruction steps; no live traffic or driver rest model."],
            }
        )
    ordered = rank_routes(comparisons)
    scope = (
        (
            "all_candidates"
            if len(routes) == 3
            and not warnings
            and all(r["status"] != "incomplete" for r in routes)
            and all(r["coverage_fraction"] >= 1 - 1e-12 for r in routes)
            else "available_candidates"
        )
        if ordered
        else "none"
    )
    reason = "No route is eligible: weather is incomplete or a No Travel hazard is forecast."
    if ordered:
        reason = (
            "Preferred by Severe miles, High miles, distance-weighted average risk, "
            "then travel time."
        )
        if len(ordered) > 1:
            first, second = ordered[:2]
            for attr, label in [
                ("severe_m", "fewer Severe miles"),
                ("high_m", "fewer High miles"),
                ("average_risk_index", "lower distance-weighted average risk"),
                ("duration_s", "shorter estimated travel time"),
            ]:
                if getattr(first, attr) != getattr(second, attr):
                    reason = f"Selected for {label} among eligible evaluated routes."
                    break
        if scope == "available_candidates":
            reason += " Provisional: some alternatives or weather evaluations are unavailable."
    if discovery.returned_count < 3 or discovery.duplicate_count:
        warnings.append(
            {
                "code": "fewer_alternatives",
                "message": (
                    f"{len(routes)} distinct truck route(s) available. "
                    "Free ORS alternatives are limited to 100 km."
                ),
            }
        )
    result = {
        "schema_version": "1",
        "request_id": str(uuid4()),
        "evaluated_at": instant(datetime.now(UTC)),
        "departure_at": instant(data["departure_at"]),
        "departure_timezone": data["departure_timezone"],
        "origin": data["origin"],
        "destination": data["destination"],
        "load_lb": data["load_lb"],
        "checkpoint_interval_mi": data["checkpoint_interval_mi"],
        "routes": routes,
        "requested_route_count": 3,
        "actual_route_count": len(routes),
        "recommendation": {
            "route_id": ordered[0].route_id if ordered else None,
            "scope": scope,
            "state": "recommended"
            if scope == "all_candidates"
            else "provisional"
            if ordered
            else "no_safe_route"
            if all(r["status"] == "no_travel" for r in routes)
            else "incomplete",
            "ordered_eligible_route_ids": [r.route_id for r in ordered],
            "reasons": [reason],
        },
        "warnings": warnings,
        "forecast_anchor_at": instant(data["departure_at"]),
        "methodology_version": "pdf-v1-conservative-endpoints",
        "limitations": [
            "Assessment prototype, not certified truck dispatch or severe-weather navigation.",
            "Cargo weight affects weather rules only; vehicle dimensions/gross weight are not set.",
        ],
    }
    try:
        result["corridor_context"] = create_context(routes, result["departure_at"], data["load_lb"])
    except ProviderError as error:
        result["warnings"].append({"code": error.code, "message": error.message})
    return result
