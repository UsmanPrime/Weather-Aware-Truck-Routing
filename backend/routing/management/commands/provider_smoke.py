"""Opt-in live evidence. Never invoked by CI and never emits authenticated URLs."""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic

from django.core.management.base import BaseCommand, CommandError

from routing.domain.forecast import forecast_at
from routing.domain.types import Coordinate
from routing.providers.errors import ProviderError
from routing.providers.here import HereRouting
from routing.providers.http import HttpTransport
from routing.providers.open_meteo import UNITS, OpenMeteo

CORRIDORS = (
    ("Chicago–Indianapolis", Coordinate(41.8781, -87.6298), Coordinate(39.7684, -86.1581)),
    ("Dallas–Houston", Coordinate(32.7767, -96.7970), Coordinate(29.7604, -95.3698)),
    ("Atlanta–Nashville", Coordinate(33.7490, -84.3880), Coordinate(36.1627, -86.7816)),
)


class Command(BaseCommand):
    help = "Run real provider proofs and optionally save sanitized JSON evidence."

    def add_arguments(self, parser):
        parser.add_argument("--provider", choices=["all", "here", "weather"], default="all")
        parser.add_argument("--output")

    def handle(self, *args, **options):
        departure = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(
            hours=1
        )
        report = {
            "data_kind": "live_provider_smoke",
            "run_at": datetime.now(UTC).isoformat(),
            "departure_at": departure.isoformat(),
            "results": {},
        }
        failed = False
        if options["provider"] in ("all", "here"):
            proofs = []
            adapter = HereRouting(os.environ.get("HERE_API_KEY", ""))
            for name, origin, destination in CORRIDORS:
                start = monotonic()
                try:
                    discovery = adapter.discover(origin, destination, departure)
                    proofs.append(
                        {
                            "corridor": name,
                            "status": "success",
                            "transport_mode": "truck",
                            "returned_count": discovery.returned_count,
                            "unique_geometry_count": len(discovery.routes),
                            "duplicate_count": discovery.duplicate_count,
                            "elapsed_s": round(monotonic() - start, 3),
                            "routes": [
                                {
                                    "distance_m": route.distance_m,
                                    "duration_s": route.duration_s,
                                    "notices": [notice.__dict__ for notice in route.notices],
                                    "sections": [
                                        {
                                            "distance_m": section.distance_m,
                                            "duration_s": section.duration_s,
                                            "travel_duration_s": section.travel_duration_s,
                                            "geometry_points": len(section.geometry),
                                            "span_count": len(section.spans),
                                            "span_total_length_m": sum(
                                                s.length_m for s in section.spans
                                            ),
                                            "span_total_duration_s": sum(
                                                s.duration_s for s in section.spans
                                            ),
                                            "span_offsets": [s.offset for s in section.spans],
                                            "span_notices": [
                                                n.__dict__ for s in section.spans for n in s.notices
                                            ],
                                            "notices": [n.__dict__ for n in section.notices],
                                        }
                                        for section in route.sections
                                    ],
                                }
                                for route in discovery.routes
                            ],
                            "checkpoint_timing_accuracy": "not established by discovery alone",
                        }
                    )
                    if len(discovery.routes) == 3:
                        break
                except ProviderError as exc:
                    failed = True
                    proofs.append(
                        {"corridor": name, "status": "blocked", "error": exc.as_dict("smoke")}
                    )
                    if exc.code in ("missing_credentials", "access_denied"):
                        break
            report["results"]["here"] = proofs
        if options["provider"] in ("all", "weather"):
            # Chicago, Bloomington IL, St Louis: representative I-55 corridor.
            points = (
                Coordinate(41.8781, -87.6298),
                Coordinate(40.4842, -88.9937),
                Coordinate(38.6270, -90.1994),
            )
            start = monotonic()
            try:
                transport = HttpTransport()
                series = OpenMeteo(transport).forecast(points)
                report["results"]["open_meteo"] = {
                    "status": "success",
                    "elapsed_s": round(monotonic() - start, 3),
                    "units_validated": UNITS,
                    "batch_size": len(series),
                    "response_bytes": transport.last_response_bytes,
                    "batch_order_check": "grid within 1 degree of corresponding request",
                    "semantics": "wind instant; rain + showers and snowfall preceding-hour sums",
                    "locations": [
                        {
                            "requested": item.requested_position.__dict__,
                            "returned_grid": item.grid_position.__dict__,
                            "hour_count": len(item.hours),
                            "first_valid_at": item.hours[0].valid_at.isoformat(),
                            "last_valid_at": item.hours[-1].valid_at.isoformat(),
                            "missing_measurements": sum(
                                value is None
                                for hour in item.hours
                                for value in hour.weather.__dict__.values()
                            ),
                            "available_frames_0_to_48": sum(
                                all(
                                    value is not None
                                    for value in forecast_at(
                                        item, departure + timedelta(hours=offset)
                                    ).weather.__dict__.values()
                                )
                                for offset in range(49)
                            ),
                            "first_normalized_hour": item.hours[0].weather.__dict__,
                        }
                        for item in series
                    ],
                }
            except ProviderError as exc:
                failed = True
                report["results"]["open_meteo"] = {
                    "status": "blocked",
                    "error": exc.as_dict("smoke"),
                }
        encoded = json.dumps(report, indent=2, ensure_ascii=True)
        if options["output"]:
            output = Path(options["output"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(encoded + "\n", encoding="utf-8")
        self.stdout.write(encoded)
        if failed:
            raise CommandError(
                "One or more live provider checks were blocked; see sanitized evidence."
            )
