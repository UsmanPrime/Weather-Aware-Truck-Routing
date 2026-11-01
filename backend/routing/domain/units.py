"""Explicit units; no rounding before risk classification."""

from math import isfinite

METERS_PER_MILE = 1609.344


def nonnegative(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if isfinite(number) and number >= 0 else None


def kmh_to_mph(value: float) -> float:
    return value / 1.609344


def mm_to_inches(value: float) -> float:
    return value / 25.4


def cm_to_inches(value: float) -> float:
    return value / 2.54


def miles_to_meters(value: float) -> float:
    return value * METERS_PER_MILE


def meters_to_miles(value: float) -> float:
    return value / METERS_PER_MILE
