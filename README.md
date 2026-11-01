# Weather-Aware Truck Routing

React + Django implementation of the [Spotter assessment](docs/fs-assessment-spotter.pdf), November 1–4, 2026.

Milestone 1 provides a working service-status frontend, database-free API, independently testable weather risk/ranking logic, provider adapters and an opt-in live provider proof. Route planning UI, checkpoint sampling/ETAs and corridor heatmap are **not implemented yet**. No fixtures are displayed as live data.

## Local development

Prerequisites: Node 24 LTS or newer, npm, Python 3.13, and [uv](https://docs.astral.sh/uv/). Lockfiles are committed. Commands below work in PowerShell; use `npm.cmd` if PowerShell policy blocks `npm`.

Backend, terminal one:

```powershell
cd backend
Copy-Item .env.example .env
uv sync --locked
uv run --env-file .env python manage.py runserver 127.0.0.1:8000
```

No database creation or migrations are required. The template explicitly enables local debug mode. With debug disabled, Django requires a configured `DJANGO_SECRET_KEY`. Debug mode's ephemeral key is development-only and unsuitable for signed corridor context across processes. Generate a stable secret before that later milestone. Never commit `.env`.

Frontend, terminal two:

```powershell
cd frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

Visit `http://127.0.0.1:5173`. Vite proxies `/api` to Django; the shell checks `GET /api/v1/health`, whose response is `{"status":"ok"}`. Health indicates process availability only, not provider access. No CORS middleware is needed for this local same-origin proxy. Deployment/CORS configuration remains later work; no deployment was authorized for this milestone.

## Verification

From `backend`, with the local `.env` created above:

```powershell
uv run --env-file .env pytest
uv run --env-file .env python manage.py check
uv run ruff check .
uv run ruff format --check .
```

From `frontend`:

```powershell
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
```

CI runs these checks with explicit local/debug settings. Tests do not call providers or need credentials. Provider fixtures are synthetic and identified in test files. Current measured results and live checks are in [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md), separate from test assertions.

## Real provider proof

Add `HERE_API_KEY` only to the server process environment or untracked `backend/.env`. Never use `VITE_` for secrets. From `backend`:

```powershell
uv run --env-file .env python manage.py provider_smoke --output ../docs/evidence/provider-smoke-local.json
# Open-Meteo is keyless; run it independently if HERE access is unavailable:
uv run --env-file .env python manage.py provider_smoke --provider weather
```

The smoke command uses real network calls. It returns a nonzero exit code for blocked providers and writes sanitized evidence even on partial failure. HERE tries Chicago–Indianapolis, Dallas–Houston and Atlanta–Nashville until it finds three distinct geometries; missing/rejected credentials stop attempts. It preserves actual returned counts and never manufactures alternatives. A successful discovery is not proof of checkpoint ETA accuracy; inspect spans and section/travel totals before implementing interpolation. Missing alternatives remain a reported assessment gap.

Open-Meteo proof batches Chicago, Bloomington IL and St Louis, checks returned grid positions against request order, validates UTC Unix timestamps and actual units, and reports missingness, coverage, bytes and latency. These are representative I-55 coordinates, **not checkpoints obtained from a verified HERE route**. Forecasts are model estimates, not live observations.

Adapters deliberately use bounded synchronous HTTP with no retries yet. End-to-end deadlines, caching, throttles and orchestration belong to the next milestone, not this proof. Authenticated URLs/upstream bodies are not printed, persisted or used in exceptions. Redirects are refused.

## Code and methodology

- `backend/routing/domain`: immutable normalized types, explicit conversions, exact PDF thresholds/load overrides, missingness-aware combination and lexicographic ranking.
- `backend/routing/providers`: HERE flexible-polyline decoding, summary/travel-summary and span metadata, Open-Meteo normalization, provider interfaces and structured failures.
- `backend/routing/api`: process health and structured DRF error handling. Provider proofs are management commands; public trip-planning endpoints are not implemented.
- `frontend/src`: React/TypeScript health shell, Tailwind tokens, typed health response parser and lazy MapLibre import boundary. The map is not rendered yet.

Boundary interpretations: continuous wind bands use 25/35/45/55 mph; overlapping rain .25/.50 and snow 1/2 thresholds choose the higher class. Rain exactly 1 in/hr and snow exactly 3 in/hr remain Severe. Load overrides use strict `>` at 30,000/40,000 lb. Combined risk is the worst hazard; missing hazards remain unknown unless a known No Travel hazard already prohibits travel. The 0–4 ordinal index is the approved average-risk encoding, not a safety probability. Ranking follows Severe distance, High distance, average index, then duration, excluding incomplete/No Travel candidates. Future route summaries must disclose provisional scope.

Detailed requirements, approved architecture, assumptions and implementation sequence remain in [ASSESSMENT](docs/ASSESSMENT.md), [ARCHITECTURE](docs/ARCHITECTURE.md), [DECISIONS](docs/DECISIONS.md) and [PLAN](docs/PLAN.md). Provider sources and unresolved timing details are recorded with milestone evidence. Maintain required provider/map attribution when their data is displayed.
