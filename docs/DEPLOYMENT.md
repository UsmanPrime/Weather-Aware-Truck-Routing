# Render deployment

The existing application uses a Python Web Service and a React Static Site:

- Frontend: https://spotter-weather-routing-jm1n.onrender.com
- Backend health: https://weather-aware-truck-routing-ddv8.onrender.com/api/v1/health

Public acceptance has been reported by the owner. Dated independently captured checks remain in [production audit](PRODUCTION_AUDIT.md) and [Pre-Loom QA](PRE_LOOM_QA.md). A GitHub commit, an older receipt and a Live Render deployment are separate facts; confirm deployment identity in each service's Events tab.

## Existing service settings

| Setting | Django Web Service | React Static Site |
|---|---|---|
| Branch / root | main / `backend` | main / `frontend` |
| Runtime | Python 3.13.17; uv 0.13.5 | Node 24.11.0 |
| Build | `uv sync --frozen --no-dev` | `npm ci && npm run build` |
| Start | `uv run --no-sync gunicorn config.wsgi:application --config gunicorn.conf.py` | No start command |
| Health / output | `/api/v1/health` | `dist` |
| Hosting | Free instance, one worker/four threads | Static CDN |

[render.yaml](../render.yaml) is the configuration reference. Automatic deployments/previews are off. Do not create duplicate services or reapply generated secrets for a normal release. There is no database, migration or collectstatic step.

## Environment

Backend environment:

| Name | Value / secure action |
|---|---|
| `PYTHON_VERSION` | `3.13.17` |
| `UV_VERSION` | `0.13.5` |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_SECRET_KEY` | Generate one strong stable value in Render; retain it across restarts. Blueprint uses `generateValue: true`. Never use a demo/example key. |
| `ROUTING_PROVIDER` | `ors` |
| `ORS_API_KEY` | Copy directly from ignored local backend/.env into the backend secret field; never into this document or frontend. |
| `ORS_BASE_URL` | `https://api.heigit.org/openrouteservice` |
| `ORS_GEOCODING_BASE_URL` | `https://api.heigit.org/pelias/v1` |
| `CORS_ALLOWED_ORIGINS` | Initially blank until the actual frontend exists, then its exact `https://` origin without a trailing slash. |
| `DJANGO_ALLOWED_HOSTS` | Optional for Render's generated hostname, which is added from `RENDER_EXTERNAL_HOSTNAME`; add actual custom hostnames explicitly if used. |

Render supplies `PORT` and `RENDER_EXTERNAL_HOSTNAME`; do not override them. Production frontend settings: `NODE_VERSION=24.11.0` and `VITE_API_BASE_URL=https://weather-aware-truck-routing-ddv8.onrender.com/api/v1`. Backend CORS: `https://spotter-weather-routing-jm1n.onrender.com` exactly, without trailing slash. No provider secret belongs on the frontend.

Keep the existing stable Django secret and server-side ORS key. Set `DJANGO_DEBUG=false`. Store replacements directly in Render secret fields; never in Git, screenshots or build commands. Custom hostnames require explicit allowed-host/CORS entries.

## Manual release

1. Run [verification](TESTING.md), review the diff and obtain push/deployment authorization. Fetch and check remote ancestry before a normal push; never overwrite remote work.
2. In each affected existing service, choose **Manual Deploy > Deploy latest commit** (or select the reviewed commit). Backend dependency/configuration changes require a backend deployment; Vite source or public environment changes require a frontend rebuild.
3. Wait for **Live**, open the deployment event and compare the SHA with the approved GitHub commit for each service. Pushing does not trigger these services automatically.
4. Verify HTTPS health and run [one bounded public acceptance](PUBLIC_ACCEPTANCE.md). Inspect desktop/tablet/mobile captures, actual route/weather details, CORS and console. Record new results with their time/commit; do not relabel an older receipt.

For initial setup in a new account, use the table and blueprint only after resource-creation approval. Choose Free Python compute and a Static Site, preserve the SPA rewrite `/*` to `/index.html` and headers from the blueprint. No database, disk, worker, paid tier or payment method is needed by the application. Stop if account-specific setup requires a paid resource/card. Free-tier policies can change; check [Render's policy](https://render.com/docs/free) before creating resources.

## Operational limits

Free services have quotas and cold starts; the frontend permits a 90-second request timeout and displays failures/retry guidance. Do not add keep-alive polling. Health reports process availability, not provider entitlement.

In-process budgets: ORS 10/minute and 100/day (two reserved units per discovery); Pelias 20/minute and 200/day; weather 150 coordinates/minute and 3,000/day. Cache TTLs: routes 300 seconds, places 86,400 seconds, weather 900 seconds. API throttles further constrain requests. Budgets/cache reset on restart and are not distributed enforcement; keep one backend process. Provider accounts remain the quota backstop.

Production trusts Render's forwarded HTTPS header only when its hostname environment is present. CORS allows exact configured origins without credentials. HSTS is host-only for one hour; `check --deploy` deliberately reports W005/W021 because subdomain coverage and preload are not enabled. Do not broaden that policy merely to silence warnings.

Linux [Gunicorn smoke](../scripts/production_smoke.py) verifies loopback health, proxy headers and CORS with an ephemeral secret and no providers. Actual hosted HTTPS and deployment SHAs still need public/dashboard verification. Preserve Open-Meteo noncommercial usage terms and all map/provider attribution.
