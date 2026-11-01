# Public acceptance procedure

Run this only after actual frontend/backend origins exist and the user approves hosting. No URLs below are live demo claims. The script calls real providers and never intercepts or substitutes data.

From `frontend`, after `npm ci` and `npx playwright install chromium`:

```powershell
$env:PUBLIC_FRONTEND_URL = 'https://ACTUAL-FRONTEND-HOST'
$env:PUBLIC_BACKEND_URL = 'https://ACTUAL-BACKEND-HOST'
node scripts/public-smoke.mjs --require-three
```

Set plain HTTPS origins, with no `/api/v1`, paths, query parameters or credentials. The script adds `/api/v1` itself. `--require-three` makes fewer than three actual routes a failed demonstration gate; omitting it records a truthful warning rather than fabricating alternatives. No ORS or Django secrets are needed in this command or browser environment.

## Request budget and behavior

One run submits **one 25-mile plan and one corridor forecast**. It verifies all three checkpoint-control options before submitting, makes two real Pelias searches, and reuses the same page/data at desktop and mobile sizes. Health/CORS checks do not call providers. The backend may use one ORS alternative request and at most its documented truck-primary fallback; weather uses bounded batches and cache. It does not retry plans, scrape corridors, run both viewport projects as separate journeys or ping the service to keep it awake.

Do not run this in routine CI. Do not loop it. If a live provider fails or returns incomplete coverage, keep the failed receipt and inspect the problem before a deliberate rerun. Existing deterministic tests cover separate 10/50-mile submitted plans, threshold extremes and failure branches without provider quota. This public run verifies the 10/25/50 controls and one genuine 25-mile submission, not three expensive submissions.

## Automated checks

- Actual frontend document and the first browser-to-Django health response, including first-request elapsed time/status. No API warm-up is issued first. A cold Render loading page/error is recorded as failure; wait for wake-up and rerun manually. A single successful run does not establish a cold-start distribution or SLA.
- HTTPS origins and HTTP-to-HTTPS redirect; exact frontend CORS, rejected untrusted origin and JSON POST preflight.
- Real Pelias autocomplete selection and destination lookup; genuine ORS truck geometries, official positive distance/duration, unique geometry hashes, route count and endpoint chainage.
- Increasing checkpoint ETAs, actual forecast source/retrieval metadata, nearest wind timestamps and preceding-hour precipitation alignment. Missing measurements are preserved rather than treated as successful live weather.
- Route/list selection, checkpoint ETA/valid-time details and recommendation explanation.
- Exactly 49 frames, +0/+48 absolute timestamps separated by 48 hours, aligned cell arrays, slider endpoints and displayed labels, fixed recommendation and one plan/corridor request across scrubbing.
- Production map canvas readiness, zoom/fit controls, desktop/mobile screenshots and mobile horizontal overflow. This production run uses UI/DOM checks, not the development-only MapLibre inspection handle; deterministic browser tests separately inspect rendered feature-state/geometry. Inspect public screenshots/tooltips for actual road and weather-layer appearance.
- Browser runtime/console/network failures; credential patterns in entry assets and credential-bearing outgoing browser URLs/headers. Generic pattern checks cannot prove absence of every secret format. Run the exact configured-secret scan against the local production assets as a separate gate:

```powershell
# Repository root; reads known secrets locally without printing them.
backend/.venv/Scripts/python.exe scripts/check_secrets.py --assets frontend/dist
```

Outputs are `frontend/test-results/public-smoke/report.json`, `desktop.png`, `mobile.png` and `mobile-forecast.png`, ignored by Git. The report omits authorization headers, query values, signed corridor context and raw provider payloads. Do not publish failed-console screenshots or terminal history until reviewed for sensitive information. Set `PUBLIC_SMOKE_OUTPUT` to choose another reviewed output directory.

## Human public review

Open the actual frontend in a normal browser. Inspect all three routes and their notices; compare checkpoint weather valid times with ETAs. Hover/click real map checkpoints and corridor cells. Scrub +0/+24/+48, confirm absolute time and displayed wind values change when forecasts differ, and confirm departure/recommendation stay fixed. Exact category colors can legitimately remain Low. Toggle weather visibility and metric; verify Unknown styling if actual missing cells exist, otherwise use the labeled deterministic test evidence.

Review desktop, tablet and phone keyboard/focus, autocomplete, form validation, selected-route emphasis, checkpoint list, map attribution, legend and footer limitations. Use the list when WebGL is unavailable. Inspect DevTools for missing assets, browser errors and keys; the API key must never appear in browser requests.

Record actual URLs, commit, time, first-request behavior and pass/fail results in a reviewed receipt before adding the demo link to README. Do not claim public acceptance until this command and human review run against real deployed services.

## Local rehearsal

`--allow-localhost` permits HTTP only for `localhost`/`127.0.0.1`; it explicitly skips public TLS/CORS assertions and labels the receipt local. A Vite preview using its local API proxy can use the preview origin for both variables. Rehearsal verifies the script and production bundle but is not hosted acceptance.
