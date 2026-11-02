# Architecture

Routecast has a React client and a database-free Django JSON API. The client owns input and presentation; Django owns provider credentials, request validation and route evaluation. [Methodology](METHODOLOGY.md) defines the calculations; [decisions](DECISIONS.md) records assumptions.

## Request flow

1. `TripForm` and `PlaceSearch` select coordinates through `GET /api/v1/geocode` (HeiGIT Pelias).
2. `POST /api/v1/plans` validates aware departure, timezone, cargo pounds and checkpoint spacing. The routing adapter requests ORS `driving-hgv` alternatives.
3. Pure geometry functions map official instruction distances/durations onto route geometry and generate checkpoints/ETAs. Forecast batches are matched to those arrivals, classified and aggregated; eligible routes are ranked.
4. React renders every returned route and keeps map/card/checkpoint selection synchronized.
5. `POST /api/v1/corridor-forecasts` accepts bounded signed context and returns up to 96 cells with 49 frames. Its independent failure does not discard the route evaluation. Scrubbing reuses data and updates feature state without a new forecast request.

`GET /api/v1/health` reports process health only; it does not probe providers or disclose secrets.

## Source boundaries

| Location | Responsibility |
|---|---|
| `backend/routing/api/` | DRF validation, bounded JSON parser, throttles, structured errors and views |
| `backend/routing/providers/` | HTTP, schema/unit validation, ORS/Pelias/Open-Meteo normalization; optional HERE |
| `backend/routing/domain/` | Deterministic geometry, forecast lookup, risk, exposure, ranking and corridor sampling |
| `backend/routing/services/` | Orchestration, bounded cache/budgets and signed context |
| `frontend/src/api/` | Fetch cancellation/deadlines and Zod response validation |
| `frontend/src/features/` | Trip, routes, map and independent forecast UI |
| `frontend/src/app/` | Application state and visual tokens/layout |

## Contracts

Use the executable definitions rather than a duplicated illustrative schema:

- [DRF serializers](../backend/routing/api/serializers.py) validate incoming places, aware timestamps, IANA zones, finite cargo and 10/25/50-mile spacing.
- [Frontend contracts](../frontend/src/api/contracts.ts) validate plan, checkpoint and corridor responses and derive TypeScript types.
- [Normalized domain types](../backend/routing/domain/types.py) define provider-neutral Python dataclasses/enums.
- [API errors](../backend/routing/api/errors.py) wrap failures with code, message, retryability and request ID. Raw provider bodies/authenticated URLs are not returned.

Coordinates use GeoJSON longitude/latitude; internal distances are metres and durations seconds. Wire fields name their units. Instants are timezone-aware; forecast lookup uses UTC. Null weather values preserve missingness.

## State and map lifecycle

`App` cancels obsolete plan/corridor requests and tracks input revisions so late results remain marked unapplied when inputs change. Place searches debounce and abort obsolete requests. MapLibre loads lazily; the map/listeners are created in one mount effect and removed on cleanup. Sources update for route/checkpoint selection; frame updates use feature state and cancel pending animation frames. A development-only inspection handle supports deterministic rendered-map tests and is absent from production.

## Resource and security bounds

Providers are fixed/validated HTTPS endpoints with timeouts and bounded responses; no client-selected upstream URL is accepted. Forecast batches contain at most 25 locations. One Gunicorn process/four threads shares in-process cache and provider budgets; restarts reset them. This is not distributed quota enforcement.

Requests are limited to 256 KiB. Uncompressed signed context expires after 30 minutes, with 128 KiB encoded / 96 KiB decoded limits, at most three routes and 6,000 coordinates. Compression is rejected. Stable server secrets preserve signature validation across restarts. Production defaults to DEBUG off, exact CORS and Render proxy-aware HTTPS handling. See [deployment](DEPLOYMENT.md) for operational constraints.
