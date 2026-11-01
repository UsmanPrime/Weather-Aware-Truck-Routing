from math import inf, nan, nextafter

import pytest

from routing.domain.risk import assess_weather, normalize_weather, rain_risk, snow_risk, wind_risk
from routing.domain.types import Risk, Weather
from routing.domain.units import (
    cm_to_inches,
    kmh_to_mph,
    meters_to_miles,
    miles_to_meters,
    mm_to_inches,
)


@pytest.mark.parametrize(
    "boundary,below,at",
    [
        (25, Risk.LOW, Risk.MODERATE),
        (35, Risk.MODERATE, Risk.HIGH),
        (45, Risk.HIGH, Risk.SEVERE),
        (55, Risk.SEVERE, Risk.NO_TRAVEL),
    ],
)
@pytest.mark.parametrize("direction", [-1, 0, 1])
def test_wind_boundaries(boundary, below, at, direction):
    value = boundary if direction == 0 else nextafter(boundary, inf if direction > 0 else -inf)
    assert wind_risk(value, 0) == (below if direction < 0 else at)


@pytest.mark.parametrize(
    "classify,boundary,below,at,above",
    [
        (rain_risk, 0.10, Risk.LOW, Risk.MODERATE, Risk.MODERATE),
        (rain_risk, 0.25, Risk.MODERATE, Risk.HIGH, Risk.HIGH),
        (rain_risk, 0.50, Risk.HIGH, Risk.SEVERE, Risk.SEVERE),
        (rain_risk, 1.0, Risk.SEVERE, Risk.SEVERE, Risk.NO_TRAVEL),
        (snow_risk, 0.5, Risk.LOW, Risk.MODERATE, Risk.MODERATE),
        (snow_risk, 1.0, Risk.MODERATE, Risk.HIGH, Risk.HIGH),
        (snow_risk, 2.0, Risk.HIGH, Risk.SEVERE, Risk.SEVERE),
        (snow_risk, 3.0, Risk.SEVERE, Risk.SEVERE, Risk.NO_TRAVEL),
    ],
)
@pytest.mark.parametrize("direction", [-1, 0, 1])
def test_precipitation_boundaries(classify, boundary, below, at, above, direction):
    value = boundary if direction == 0 else nextafter(boundary, inf if direction > 0 else -inf)
    assert classify(value) == {-1: below, 0: at, 1: above}[direction]


@pytest.mark.parametrize(
    "wind,load,expected",
    [
        (45, 29999.99, Risk.SEVERE),
        (45, 30000, Risk.SEVERE),
        (45, 30000.01, Risk.NO_TRAVEL),
        (54.999, 30000, Risk.SEVERE),
        (54.999, 30000.01, Risk.NO_TRAVEL),
        (35, 39999.99, Risk.HIGH),
        (35, 40000, Risk.HIGH),
        (35, 40000.01, Risk.SEVERE),
        (44.999, 40000, Risk.HIGH),
        (44.999, 40000.01, Risk.SEVERE),
        (34.999, 100000, Risk.MODERATE),
        (24.999, 100000, Risk.LOW),
        (55, 0, Risk.NO_TRAVEL),
        (55, 30000, Risk.NO_TRAVEL),
        (55, 40000, Risk.NO_TRAVEL),
        (80, 100000, Risk.NO_TRAVEL),
        (0, 0, Risk.LOW),
    ],
)
def test_load_exact_equality_and_decimal_wind(wind, load, expected):
    assert wind_risk(wind, load) == expected


@pytest.mark.parametrize("invalid", [None, -1, nan, inf, -inf, True, "25"])
def test_invalid_weather_is_unknown(invalid):
    assert wind_risk(invalid, 0) is None
    assert rain_risk(invalid) is None
    assert snow_risk(invalid) is None


@pytest.mark.parametrize("invalid", [None, -1, nan, inf, True, "30000"])
def test_invalid_load_rejected(invalid):
    with pytest.raises(ValueError):
        wind_risk(10, invalid)


@pytest.mark.parametrize(
    "weather,load,expected,missing",
    [
        (Weather(0, 0, 0), 0, Risk.LOW, ()),
        (Weather(35, 0.5, 1), 0, Risk.SEVERE, ()),
        (Weather(45, 0.1, 0), 30001, Risk.NO_TRAVEL, ()),
        (Weather(None, 0, 0), 0, None, ("wind_mph",)),
        (Weather(0, None, 0), 0, None, ("rain_in_per_hr",)),
        (Weather(None, 1.1, None), 0, Risk.NO_TRAVEL, ("wind_mph", "snow_in_per_hr")),
        (Weather(55, None, None), 0, Risk.NO_TRAVEL, ("rain_in_per_hr", "snow_in_per_hr")),
    ],
)
def test_combined_severity_preserves_unknowns(weather, load, expected, missing):
    result = assess_weather(weather, load)
    assert result.risk == expected
    assert result.missing_fields == missing


def test_normalization_uses_liquid_components_not_total_precipitation():
    result = normalize_weather(wind_kmh=16.09344, rain_mm=2.54, showers_mm=2.54, snow_cm=2.54)
    assert result.wind_mph == pytest.approx(10)
    assert result.rain_in_per_hr == pytest.approx(0.2)
    assert result.snow_in_per_hr == pytest.approx(1)


@pytest.mark.parametrize("field", ["wind_kmh", "rain_mm", "showers_mm", "snow_cm"])
@pytest.mark.parametrize("invalid", [None, -1, nan, inf, True])
def test_normalization_preserves_missing_and_invalid(field, invalid):
    values = {"wind_kmh": 0, "rain_mm": 0, "showers_mm": 0, "snow_cm": 0, field: invalid}
    weather = normalize_weather(**values)
    target = (
        "wind_mph"
        if field == "wind_kmh"
        else ("snow_in_per_hr" if field == "snow_cm" else "rain_in_per_hr")
    )
    assert getattr(weather, target) is None


def test_unit_conversions():
    assert kmh_to_mph(1.609344) == pytest.approx(1)
    assert mm_to_inches(25.4) == pytest.approx(1)
    assert cm_to_inches(2.54) == pytest.approx(1)
    assert miles_to_meters(50) == pytest.approx(80467.2)
    assert meters_to_miles(1609.344) == pytest.approx(1)


def test_extreme_invalid_numbers_do_not_overflow_or_become_known_weather():
    weather = normalize_weather(wind_kmh=10**1000, rain_mm=1e308, showers_mm=1e308, snow_cm=0)
    assert weather.wind_mph is None
    assert weather.rain_in_per_hr is None


@pytest.mark.parametrize("load", [0, 30000, 30001, 40000, 40001])
def test_increasing_wind_never_decreases_risk(load):
    risks = [wind_risk(wind / 10, load) for wind in range(701)]
    assert risks == sorted(risks)
