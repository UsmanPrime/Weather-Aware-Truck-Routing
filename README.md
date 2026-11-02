# Routecast

Routecast compares truck routes using the weather expected when the truck reaches each road-distance checkpoint. It combines genuine routing alternatives, cargo-sensitive weather rules and an independent corridor forecast to make route tradeoffs and missing data visible. Built with React and Django for the Spotter full-stack assessment.

[Live application](https://spotter-weather-routing-jm1n.onrender.com) ? [GitHub repository](https://github.com/UsmanPrime/Weather-Aware-Truck-Routing) ? [Technical documentation](docs/README.md)

![Routecast with genuine truck routes and captured Open-Meteo forecasts](docs/screenshots/pre-loom/after-results-1440.png)

Screenshot: corrected local application rendering captured live responses with real basemap tiles; this is replay evidence, not a fresh hosted forecast. [Capture details](docs/PRE_LOOM_QA.md).

## Capabilities

- Genuine OpenRouteService **driving-hgv** alternatives, with official distance/duration and instruction timing. Fewer available routes are reported honestly.
- Checkpoints every **10, 25 or 50 miles** along road geometry, with arrival-specific wind, rain and snowfall forecasts.
- Load-sensitive risk, distance-weighted exposure and an explained recommendation; incomplete forecasts remain unknown.
- Interactive route/checkpoint selection, weather inspection, accessible lists and explicit departure timezone.
- **49 preloaded corridor frames**, from departure through +48 hours. Scrubbing changes corridor weather without changing the ETA-based recommendation.

## Architecture

React 19, TypeScript, Vite and Tailwind CSS provide the interface. MapLibre GL JS renders OpenFreeMap tiles. Django REST Framework validates requests and coordinates server-side ORS/Pelias and Open-Meteo adapters. Pure Python modules handle sampling, weather classification and ranking. There is no database, queue or account system.

```text
React planner -> Django API -> truck routes -> checkpoints and ETAs
                                      -> arrival forecasts -> risk and ranking
React forecast slider <- bounded corridor forecast <- Open-Meteo
```

[Architecture and contracts](docs/ARCHITECTURE.md) ? [Evaluation methodology](docs/METHODOLOGY.md)

## How evaluation works

Official instruction distances and durations are distributed along their road geometry. Open-Meteo wind uses the nearest hourly instant within 30 minutes; rain and snowfall use the preceding-hour accumulation containing the checkpoint ETA. Rain and showers are distinct liquid components; snowfall is new-snow depth.

The worst applicable hazard determines checkpoint risk, including the assessment's strict cargo-weight wind overrides. Each road interval receives the worse endpoint classification. Complete eligible routes rank lexicographically by **Severe miles, High miles, distance-weighted average risk, then travel time**. No Travel disqualifies a route; missing data prevents a definitive assessment. The corridor forecast is evaluated independently.

## Local development

Requires Python 3.13, [uv](https://docs.astral.sh/uv/) and Node 24 with npm. From the repository root:

```powershell
python scripts/init_env.py
cd backend
uv sync --locked
# Set ORS_API_KEY in the ignored backend/.env.
uv run --env-file .env python manage.py runserver 127.0.0.1:8000
```

The initializer preserves existing values and generates a local Django secret without printing it. In another terminal, from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to Django. No migrations are required. The Fort Worth-Dallas example fills inputs; generating routes calls real providers.

## Environment

| Variable | Purpose |
|---|---|
| `ORS_API_KEY` | Backend secret, supplied through ignored `.env` or hosting environment |
| `ROUTING_PROVIDER` | `ors` by default; optional legacy HERE adapter remains available |
| `ORS_BASE_URL` | `https://api.heigit.org/openrouteservice` |
| `ORS_GEOCODING_BASE_URL` | `https://api.heigit.org/pelias/v1` |
| `DJANGO_DEBUG` | `true` locally; `false` in production |
| `DJANGO_SECRET_KEY` | Stable backend secret for signed corridor context |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts; Render adds its supplied hostname |
| `CORS_ALLOWED_ORIGINS` | Exact frontend origins; blank for local Vite proxy |
| `VITE_API_BASE_URL` | Public API URL; defaults to `/api/v1` locally |

See the placeholder-only [backend template](backend/.env.example), [frontend template](frontend/.env.example) and [deployment settings](docs/DEPLOYMENT.md). Provider credentials never belong in Vite variables.

## Tests and checks

From `backend`:

```powershell
uv run --env-file .env pytest
uv run ruff check . ../scripts
uv run ruff format --check . ../scripts
uv run --env-file .env python manage.py check
uv lock --check --offline
uv run python ../scripts/check_secrets.py --assets ../frontend/dist
```

From `frontend` (build before the asset scan above):

```powershell
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:e2e
npm audit --omit=dev
```

[Testing guide](docs/TESTING.md) explains deterministic fixtures, Linux Gunicorn checks and opt-in provider/public verification. Routine tests make no provider calls.

## Deployment

The application uses an existing Render Python Web Service and Static Site. [Deployment instructions](docs/DEPLOYMENT.md) cover build/start commands, secrets, CORS and manual releases. [render.yaml](render.yaml) declares Free backend compute with automatic deployments and previews off. Pushing GitHub does not deploy these services automatically.

## Limitations

This assessment prototype is not certified truck dispatch or severe-weather navigation. Cargo weight is not gross vehicle weight; physical truck dimensions and legal restrictions are not configured. ETAs exclude live traffic, breaks and driver-hours rules. Forecasts and interval exposure are estimates.

Public alternatives are limited to 100 km and cannot be guaranteed for arbitrary journeys. Departure is limited to six days; later arrivals or +48-hour frames can exceed coverage and remain unknown. Corridor sampling is bounded at 96 cells, signed context at 6,000 coordinates; polar/dateline corridors are rejected. WebGL is needed for the map; route/checkpoint lists remain usable without it. Free services have quotas and cold starts; process-local caches/budgets reset on restart.

## Providers and permissions

Routing/geocoding: openrouteservice.org and Pelias by HeiGIT, using OpenStreetMap data. Forecasts: [Open-Meteo](https://open-meteo.com/) under CC BY 4.0 and its noncommercial free-service terms. Basemap: OpenFreeMap / OpenMapTiles / OpenStreetMap; attribution remains visible.

No project software license has been selected. The owner should also confirm permission to redistribute the [original assessment PDF](docs/fs-assessment-spotter.pdf); its presence does not establish redistribution rights.

The Loom recording is pending. The [walkthrough outline](docs/WALKTHROUGH.md) is not a recorded video.
