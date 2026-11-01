# Free hosting and release instructions

Status: GitHub publication is authorized and the reviewed main branch has been pushed. See RELEASE.md for exact commit/CI evidence. No cloud resources have been created and no hosted deployment has occurred. Public app URLs remain unverified; cloud creation still needs separate explicit approval.

## Cost and provider checks (November 1, 2026)

Render documents free Python web services and free static sites. Free web services idle after 15 minutes, may take about a minute to wake, and receive a shared 750 instance-hours/month. Bandwidth and build minutes also have quotas. Without a payment method, exhausted quotas suspend services/builds rather than billing. Its published free-tier overview states no credit card is required. Keep the workspace without a payment method; choose only Free, disable automatic deploys/previews, and stop if the account requests a paid plan/card. No guarantee is made about account-specific eligibility. [Free-service policy](https://render.com/docs/free), [Render overview](https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026).

HeiGIT's public account plan page was rendered in Chromium: Standard is €0, directions 2,000/day and 40/minute, geocoding 3,000/day and 100/minute. Alternative routes are limited to 100 km and three targets. The app uses only the configured free API host, with no paid failover. [Plans](https://account.heigit.org/info/plans), [restrictions](https://openrouteservice.org/restrictions/).

Open-Meteo's free endpoint is for noncommercial use with published limits of 10,000/day, 5,000/hour and 600/minute. This prototype has no advertisements, subscriptions or sales. Commercial/promotional reuse needs a separate terms review. Multi-location use is budgeted by coordinate, conservatively. [Terms](https://open-meteo.com/en/terms). OpenFreeMap provides the public map style without an API key; preserve its built-in attribution.

## Prepared service configuration

[render.yaml](../render.yaml) declares one **Free** Python service and one static site, with automatic deployments/previews off. It creates no database, disk, Redis, worker or other service. The backend uses one Gunicorn process/four threads and a shared in-process bounded cache; adding processes requires reconsidering budget coordination.

| Setting | Django web service | React static site |
|---|---|---|
| Root directory | `backend` | `frontend` |
| Runtime | Python 3.13.17; uv 0.13.5 | Node 24.11.0 |
| Build | `uv sync --frozen --no-dev` | `npm ci && npm run build` |
| Start | `uv run --no-sync gunicorn config.wsgi:application --config gunicorn.conf.py` | Static CDN; no start command |
| Output / health | `/api/v1/health` | `dist` |
| Compute | Explicit `free` | Static site; no compute plan |

Django serves JSON only, with no admin, database or static assets. There is no migrate/collectstatic step. Frontend assets/MapLibre worker are bundled by Vite and served by the static site. Gunicorn targets Linux; Windows development uses Django runserver. The Windows run verifies Django behavior and build output, not a deployed Linux Gunicorn process.

## Manual release sequence after approval

1. Review the local commit(s), passing checks and secret scan. Obtain approval to push `main`, then push to the configured GitHub origin. Do not infer push approval from this document.
2. In a payment-method-free Render workspace, create the Python web service from the repo with the table's settings and Free selected. Keep auto-deploy off. Alternatively review/apply the prepared blueprint after approval; first deployment still publishes the application.
3. Set `DJANGO_DEBUG=false`, generate a stable `DJANGO_SECRET_KEY` in Render, and copy ORS_API_KEY directly from the untracked local environment into the backend secret field. Never place secrets in YAML, frontend variables, screenshots or build commands. Set the ORS URLs and provider exactly as in the template.
4. Note the actual backend hostname. Render supplies `RENDER_EXTERNAL_HOSTNAME`; settings add that hostname to ALLOWED_HOSTS and trust Render's HTTPS proxy. Custom domains require explicit `DJANGO_ALLOWED_HOSTS` entries. Confirm public HTTPS health returns `{"status":"ok"}`.
5. Create the static site with the table's settings and set `VITE_API_BASE_URL=https://ACTUAL-BACKEND.onrender.com/api/v1`. This variable is public and contains no key. Configure the SPA rewrite and headers from the blueprint.
6. Set backend `CORS_ALLOWED_ORIGINS=https://ACTUAL-FRONTEND.onrender.com` (no trailing slash), then manually restart/redeploy the backend as needed. Only exact listed origins receive CORS permission. Cookies/credentialed CORS are disabled.
7. Visit the actual frontend. Run the Fort Worth–Dallas example, confirm three distinct truck routes, checkpoint details and forecast frames 0 and 48. Check API errors, attribution, desktop/mobile layout and browser console. Record actual URLs, timestamps and any cold-start delay before adding the demo link to README.
8. Record the 5–10 minute Loom video using [WALKTHROUGH.md](WALKTHROUGH.md); add the real link after checking its accessibility. Never label the outline as a recorded video.

## Exact manual environment settings

Create no resources until separately approved. In Render choose **New > Web Service**, connect GitHub (grant access to this repository only if possible), select `UsmanPrime/Weather-Aware-Truck-Routing`, branch `main`, root `backend`, Python runtime and **Free** instance. Use the build/start/health settings in the table above and turn auto-deploy off. Do not use a generic Django template that adds a database.

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

Render supplies `PORT` and `RENDER_EXTERNAL_HOSTNAME`; do not invent or override their values. No DATABASE_URL, Redis, HERE key, frontend provider secret or payment method is required.

Once the backend is healthy, choose **New > Static Site**, connect the same repository/main, root `frontend`, build `npm ci && npm run build`, publish `dist`, and turn auto-deploy off. Static sites have no paid compute instance; do not change the runtime to a Node web service. Set `NODE_VERSION=24.11.0` and `VITE_API_BASE_URL` to the **actual backend HTTPS origin plus `/api/v1`**. Changing this Vite value requires a frontend rebuild. Add rewrite `/*` to `/index.html` and the four response headers from render.yaml. Set backend CORS to the actual new frontend origin and restart/redeploy the backend manually.

Verify the real backend `/api/v1/health` returns JSON status ok over HTTPS. Then run [PUBLIC_ACCEPTANCE.md](PUBLIC_ACCEPTANCE.md) with both actual origins. Record URLs only after the public checks pass; no sample hostname in these instructions is a live deployment.

## Strongest local deployment proof

`python scripts/production_smoke.py` runs on Linux from any working directory with the locked backend environment. It starts the actual Gunicorn configuration, checks health/security headers, HTTP-to-HTTPS redirect, allowed/rejected CORS origins and a JSON POST preflight, then stops its process. It uses a freshly generated local secret and no provider requests. This check is included in Linux GitHub Actions. It does not prove actual Render TLS/proxy configuration; public acceptance still needs real service URLs.

## Limits and operational behavior

Conservative local budgets: routing 10/minute and 100/day (two units reserved for a possible truck-primary fallback), geocoding 20/minute and 200/day, weather 150 coordinates/minute and 3,000/day. Per-client API throttles further constrain plans/corridors/geocoding. Cache TTLs are 5 minutes for ORS geometry, 24 hours for places and 15 minutes for weather series. Retrieval timestamps remain visible. No expired-weather fallback is used. Provider failures yield structured errors/unknowns rather than fixtures or zero weather.

Budgets/cache reset with process restarts and are not distributed enforcement. Keep one process/service and do not scale this prototype. Provider account limits remain the final backstop; the app cannot charge or upgrade plans. Monitor the free dashboard during the assessment and pause the service before exceeding hosting usage. Do not add paid capacity or a keep-alive ping service.

Cold-start loading pages can precede Django. The client handles unreadable/error responses truthfully; retry after the backend wakes. Stable secrets keep signed contexts valid across restarts until their 30-minute expiry; weather/cache may need fetching again. Health checks indicate process health, not provider entitlement or quota availability.

Before release run `DJANGO_DEBUG=false` with a generated secret and `python manage.py check --deploy`. Local tests cover HTTPS redirects, security headers, exact-origin CORS and request-size/error behavior. Public TLS, actual CORS hostnames, Linux process startup and Render account eligibility still require hosted verification.

The production check exits 0 with two intentional HSTS warnings: W005 (subdomain coverage) and W021 (preload). They are not silenced. Until the actual hostname and all subordinate hosts are verified, the configuration limits HSTS to that host for one hour and does not opt into preload. Decide whether to enable broader/longer HSTS after hosted verification, rather than changing policy merely to remove warnings. The client allows up to 90 seconds for a cold first request and retains explicit failure/retry states.
