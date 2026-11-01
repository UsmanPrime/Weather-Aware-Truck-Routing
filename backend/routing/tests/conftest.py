"""Synthetic provider fixtures only. These are not recorded observations or live routes."""

from datetime import UTC, datetime

import flexpolyline
import pytest


@pytest.fixture(autouse=True)
def block_live_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError(
            "Unit tests must not call live providers; use the opt-in smoke commands."
        )

    monkeypatch.setattr("socket.create_connection", blocked)


@pytest.fixture
def here_payload():
    return {
        "routes": [
            {
                "id": "synthetic-route",
                "sections": [
                    {
                        "id": "synthetic-section",
                        "polyline": flexpolyline.encode(
                            [(41.0, -87.0), (41.1, -87.1), (41.2, -87.2)]
                        ),
                        "summary": {"length": 30000, "duration": 2400},
                        "travelSummary": {"length": 30000, "duration": 2300},
                        "spans": [
                            {
                                "offset": 0,
                                "length": 10000,
                                "duration": 900,
                                "dynamicSpeedInfo": {"trafficSpeed": 11.1},
                            },
                            {
                                "offset": 1,
                                "length": 20000,
                                "duration": 1400,
                                "dynamicSpeedInfo": {"trafficSpeed": 14.3},
                            },
                        ],
                        "notices": [{"code": "synthetic-restriction", "severity": "critical"}],
                    }
                ],
            }
        ]
    }


@pytest.fixture
def weather_payload():
    start = int(datetime(2026, 11, 1, tzinfo=UTC).timestamp())
    return {
        "latitude": 41.0,
        "longitude": -87.0,
        "utc_offset_seconds": 0,
        "hourly_units": {
            "time": "unixtime",
            "wind_speed_10m": "km/h",
            "rain": "mm",
            "showers": "mm",
            "snowfall": "cm",
        },
        "hourly": {
            "time": [start, start + 3600, start + 7200],
            "wind_speed_10m": [16.09344, 32.18688, 0],
            "rain": [2.54, 0, None],
            "showers": [2.54, 0, 0],
            "snowfall": [2.54, 0, None],
        },
    }
