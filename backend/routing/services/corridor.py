from datetime import UTC, datetime, timedelta
from time import monotonic

from routing.domain.corridor import cell_positions, corridor_grid
from routing.domain.forecast import forecast_at
from routing.domain.risk import assess_weather
from routing.providers.errors import ProviderError

from .context import read_context
from .forecasts import load_forecasts
from .planning import instant


def corridor_forecast(token: str, *, forecasts_provider=None) -> dict:
    context = read_context(token)
    try:
        cells, spacing, width = corridor_grid(context["routes"])
    except ValueError as error:
        raise ProviderError("corridor", "grid_limit", str(error), 422) from None
    positions = cell_positions(cells)
    series, warnings = load_forecasts(
        positions, provider=forecasts_provider, deadline=monotonic() + 25
    )
    departure = datetime.fromisoformat(context["departure_at"].replace("Z", "+00:00"))
    frames = []
    for offset in range(49):
        at = departure + timedelta(hours=offset)
        frame = {
            "valid_at": instant(at),
            "wind_mph": [],
            "rain_in_per_hr": [],
            "snow_in_per_hr": [],
            "risk": [],
            "wind_valid_at": [],
            "precipitation_interval_end": [],
            "coverage_fraction": 0,
        }
        complete = 0
        for position in positions:
            selected = forecast_at(series[position], at) if position in series else None
            weather = selected.weather if selected else None
            risk = assess_weather(weather, context["load_lb"]) if weather else None
            complete += int(risk is not None and not risk.missing_fields)
            for field in ("wind_mph", "rain_in_per_hr", "snow_in_per_hr"):
                frame[field].append(getattr(weather, field) if weather else None)
            frame["risk"].append(risk.risk.name.lower() if risk and risk.risk is not None else None)
            frame["wind_valid_at"].append(
                instant(selected.wind_valid_at) if selected and selected.wind_valid_at else None
            )
            frame["precipitation_interval_end"].append(
                instant(selected.precipitation_end)
                if selected and selected.precipitation_end
                else None
            )
        frame["coverage_fraction"] = complete / len(cells)
        frames.append(frame)
    for cell, position in zip(cells, positions, strict=True):
        data = series.get(position)
        cell["model_position"] = (
            [data.grid_position.longitude, data.grid_position.latitude] if data else None
        )
        cell["retrieved_at"] = instant(data.retrieved_at) if data else None
    missing = [i for i, frame in enumerate(frames) if frame["coverage_fraction"] < 1]
    if missing:
        warnings.append(
            {
                "code": "incomplete_heatmap",
                "message": (
                    f"{len(missing)} forecast frames have unavailable cells. "
                    "Route ETA assessment is unchanged."
                ),
            }
        )
    retrieved = [s.retrieved_at for s in series.values()]
    return {
        "anchor_at": instant(departure),
        "load_lb": context["load_lb"],
        "corridor_half_width_m": width,
        "grid_spacing_m": spacing,
        "cells": cells,
        "frames": frames,
        "retrieved_at": instant(max(retrieved)) if retrieved else None,
        "oldest_retrieved_at": instant(min(retrieved)) if retrieved else None,
        "source": "open_meteo",
        "data_kind": "forecast",
        "frames_with_missing_data": missing,
        "generated_at": instant(datetime.now(UTC)),
        "warnings": warnings,
    }
