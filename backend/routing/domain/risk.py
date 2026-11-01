"""PDF thresholds; ambiguous shared endpoints follow documented D02/D03."""

from dataclasses import dataclass

from .types import Risk, Weather
from .units import cm_to_inches, kmh_to_mph, mm_to_inches, nonnegative


def normalize_weather(
    *, wind_kmh: object, rain_mm: object, showers_mm: object, snow_cm: object
) -> Weather:
    wind, rain, showers, snow = map(nonnegative, (wind_kmh, rain_mm, showers_mm, snow_cm))
    liquid = nonnegative(rain + showers) if rain is not None and showers is not None else None
    return Weather(
        kmh_to_mph(wind) if wind is not None else None,
        mm_to_inches(liquid) if liquid is not None else None,
        cm_to_inches(snow) if snow is not None else None,
    )


def wind_risk(wind_mph: object, load_lb: float) -> Risk | None:
    if nonnegative(load_lb) is None:
        raise ValueError("Load must be a finite, nonnegative number of pounds")
    wind = nonnegative(wind_mph)
    if wind is None:
        return None
    if wind >= 55 or (wind >= 45 and load_lb > 30_000):
        return Risk.NO_TRAVEL
    if wind >= 45 or (wind >= 35 and load_lb > 40_000):
        return Risk.SEVERE
    if wind >= 35:
        return Risk.HIGH
    return Risk.MODERATE if wind >= 25 else Risk.LOW


def rain_risk(value: object) -> Risk | None:
    rain = nonnegative(value)
    if rain is None:
        return None
    if rain > 1:
        return Risk.NO_TRAVEL
    if rain >= 0.5:
        return Risk.SEVERE
    if rain >= 0.25:
        return Risk.HIGH
    return Risk.MODERATE if rain >= 0.10 else Risk.LOW


def snow_risk(value: object) -> Risk | None:
    snow = nonnegative(value)
    if snow is None:
        return None
    if snow > 3:
        return Risk.NO_TRAVEL
    if snow >= 2:
        return Risk.SEVERE
    if snow >= 1:
        return Risk.HIGH
    return Risk.MODERATE if snow >= 0.5 else Risk.LOW


@dataclass(frozen=True)
class RiskAssessment:
    risk: Risk | None
    wind: Risk | None
    rain: Risk | None
    snow: Risk | None
    missing_fields: tuple[str, ...]


def assess_weather(weather: Weather, load_lb: float) -> RiskAssessment:
    hazards = (
        wind_risk(weather.wind_mph, load_lb),
        rain_risk(weather.rain_in_per_hr),
        snow_risk(weather.snow_in_per_hr),
    )
    missing = tuple(
        field
        for field, risk in zip(
            ("wind_mph", "rain_in_per_hr", "snow_in_per_hr"), hazards, strict=True
        )
        if risk is None
    )
    combined = (
        Risk.NO_TRAVEL
        if Risk.NO_TRAVEL in hazards
        else None
        if missing
        else max(risk for risk in hazards if risk is not None)
    )
    return RiskAssessment(combined, *hazards, missing)
