"""Fetch real corridor weather over a previously recorded genuine route plan."""

import hashlib
import json
from pathlib import Path
from time import monotonic

from django.core.management.base import BaseCommand

from routing.services.context import create_context
from routing.services.corridor import corridor_forecast


class Command(BaseCommand):
    help = "Live weather proof using recorded real road geometry; makes no extra routing requests."

    def add_arguments(self, parser):
        parser.add_argument("--plan-file", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        plan = json.loads(Path(options["plan_file"]).read_text(encoding="utf-8"))
        token = create_context(plan["routes"], plan["departure_at"], plan["load_lb"])
        start = monotonic()
        data = corridor_forecast(token)
        summaries = []
        for i, frame in enumerate(data["frames"]):
            wind = [v for v in frame["wind_mph"] if v is not None]
            summaries.append(
                {
                    "hour": i,
                    "valid_at": frame["valid_at"],
                    "coverage_fraction": frame["coverage_fraction"],
                    "wind_range_mph": [min(wind), max(wind)] if wind else None,
                    "measurement_digest": hashlib.sha256(
                        json.dumps(frame, sort_keys=True).encode()
                    ).hexdigest(),
                    "sample_wind_valid_at": next((t for t in frame["wind_valid_at"] if t), None),
                    "sample_precipitation_end": next(
                        (t for t in frame["precipitation_interval_end"] if t), None
                    ),
                }
            )
        evidence = {
            "kind": "live_open_meteo_corridor",
            "route_geometry_source": options["plan_file"],
            "anchor_at": data["anchor_at"],
            "retrieved_at": data["retrieved_at"],
            "source": data["source"],
            "grid_cells": len(data["cells"]),
            "grid_spacing_m": data["grid_spacing_m"],
            "frame_count": len(data["frames"]),
            "api_json_bytes": len(json.dumps(data, separators=(",", ":")).encode()),
            "elapsed_s": round(monotonic() - start, 3),
            "frames": summaries,
            "warnings": data["warnings"],
        }
        Path(options["output"]).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        self.stdout.write(
            json.dumps({key: value for key, value in evidence.items() if key != "frames"}, indent=2)
        )
