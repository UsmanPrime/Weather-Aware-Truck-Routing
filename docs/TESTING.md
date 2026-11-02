# Testing and verification

Run commands from the specified directory. Use the locked Python/npm environments. Routine tests block/intercept provider traffic and require no live key. Historical results in audit reports are timestamped evidence, not assertions about future changes.

## Backend

From `backend`, after `uv sync --locked`:

```powershell
$env:DJANGO_DEBUG='true'
uv run pytest
uv run ruff check . ../scripts
uv run ruff format --check . ../scripts
uv run python manage.py check
uv lock --check --offline
```

Alternatively load the initialized local `.env` for tests/checks. Test coverage includes exact weather/load equality, missingness, ranking counterexamples, distance/time conservation, multi-section sampling, ETA/forecast intervals, provider failures, quotas, validation and signed-context bounds. `test_http_api.py` and `test_corridor.py` cover structured HTTP 413.

For deployment checks, run `uv run --env-file .env python manage.py check --deploy` with `DJANGO_DEBUG=false` and valid production host/secret configuration. Do not print secrets. Two intentional HSTS warnings are documented in [deployment](DEPLOYMENT.md).

On Linux with the locked backend environment, run `python ../scripts/production_smoke.py` from `backend`. It starts/stops real Gunicorn and checks five loopback/proxy/CORS behaviors. It does not prove public TLS. CI runs this on Linux.

For a dependency audit without adding project dependencies:

```powershell
uv export --frozen --no-dev --format requirements-txt --output-file ../.cache/runtime-requirements.txt
uvx pip-audit -r ../.cache/runtime-requirements.txt --no-deps --disable-pip
```

## Frontend

From `frontend`, after `npm ci`:

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

Vitest checks contracts, API errors, forecast features and timezone conversion. Playwright uses explicitly synthetic responses and an empty basemap while rendering actual MapLibre sources/layers. It covers selection, slider independence, request races, errors, missing/No Travel data, WebGL fallback, keyboard/Axe and responsive states. Run suites serially; Playwright cleans `test-results`. Axe does not replace screen-reader or human visual review. `npm audit` includes development tools; investigate findings before changing dependencies, and do not use force upgrades blindly.

## Repository checks

After the frontend build, from the root:

```powershell
backend/.venv/Scripts/python.exe scripts/check_secrets.py --assets frontend/dist
git diff --check
```

On other systems use the corresponding backend Python executable. The scanner checks tracked files, reachable history, focused credential patterns and configured local secrets without printing matches. It is not a guarantee for every secret format. Build assets, `.env`, caches and temporary browser output must remain ignored.

## Opt-in live verification

[Public acceptance](PUBLIC_ACCEPTANCE.md) uses the actual hosted origins and one real plan/corridor, with a strict optional three-route demonstration gate. Run after deployment, not in routine CI or repeatedly while editing. Its output belongs in ignored `.cache/public-smoke`; review before publishing evidence.

Additional retained tools serve distinct scopes:

| Tool | Purpose |
|---|---|
| `provider_smoke` management command | Sanitized adapter proof; bounded corridors, no fabricated alternatives |
| `journey_smoke` | Real local Django routing/weather pipeline |
| `corridor_smoke` | Real independent corridor from a plan file |
| `frontend/scripts/live-browser.mjs` | Real local browser journey/screenshots; requires running Django/Vite |
| `frontend/scripts/public-smoke.mjs` | Hosted HTTPS/CORS/UI/security acceptance |
| `scripts/init_env.py` | Initialize ignored local environment while preserving credentials |
| `scripts/check_secrets.py` | Source/history/asset scanning |
| `scripts/production_smoke.py` | Real Linux server configuration check |

Use `uv run --env-file .env python manage.py <command> --help` from `backend` for live command arguments. Live tools may overwrite named receipts/screenshots: use ignored output paths where supported and review provenance before committing. Never describe replayed/synthetic weather as new live observations. The optional HERE adapter and tests remain for compatibility; default deployment requires only ORS credentials.
