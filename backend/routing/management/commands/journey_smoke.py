"""Bounded live end-to-end backend proof for the verified free-provider corridor."""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand

from routing.providers.ors import PeliasGeocoding
from routing.services.planning import plan_trip


class Command(BaseCommand):
    help = "Run one real Fort Worth–Dallas plan and two Pelias searches; never run in CI."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        adapter = PeliasGeocoding(os.environ.get("ORS_API_KEY", ""))
        geocoding = {
            query: len(adapter.search(query)) for query in ("Fort Worth Texas", "Dallas Texas")
        }
        departure = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(
            hours=1
        )
        data = {
            "origin": {
                "id": "smoke-origin",
                "label": "Fort Worth, Texas",
                "position": [-97.3308, 32.7555],
            },
            "destination": {
                "id": "smoke-destination",
                "label": "Dallas, Texas",
                "position": [-96.7970, 32.7767],
            },
            "departure_at": departure,
            "departure_timezone": "America/Chicago",
            "load_lb": 30000,
            "checkpoint_interval_mi": 10,
        }
        plan = plan_trip(data)
        output = Path(options["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        self.stdout.write(
            json.dumps(
                {
                    "data_kind": "live_backend_pipeline",
                    "geocoding_counts": geocoding,
                    "actual_route_count": plan["actual_route_count"],
                    "recommendation": plan["recommendation"],
                    "routes": [
                        {
                            "distance_m": r["distance_m"],
                            "duration_s": r["duration_s"],
                            "checkpoints": len(r["checkpoints"]),
                            "coverage": r["coverage_fraction"],
                            "status": r["status"],
                            "exposure_error_m": sum(r["risk_distance_m"].values())
                            + r["unknown_distance_m"]
                            - r["distance_m"],
                        }
                        for r in plan["routes"]
                    ],
                    "warnings": plan["warnings"],
                },
                indent=2,
            )
        )
