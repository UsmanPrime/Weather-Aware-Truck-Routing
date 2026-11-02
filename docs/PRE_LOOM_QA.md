# Pre-Loom QA - November 1, 2026

> Dated record: deployment status and test counts below describe the recorded run. Use the [documentation index](README.md) for current setup, architecture and operations.

Decision: **local fixes verified; public release still required before recording the final Loom**. No push or deployment was performed. This audit is evidence of the specific checks below, not certification of dispatch safety or exhaustive browser/security coverage.

## Baselines and evidence provenance

Public frontend: https://spotter-weather-routing-jm1n.onrender.com

Public backend: https://weather-aware-truck-routing-ddv8.onrender.com

Deployed application: `c87bc89cfdfb39529f249fbddb2891b170d15a4e` (both services previously confirmed by owner). Starting local HEAD: `e369532`, with `ca9d1ab` and `e369532` unpublished documentation commits preserved. Source/UI correction: `6488b1f`. Backend security correction: `712f833`. Public behavior below was measured against the old deployment, not the corrected source.

Read the two-page PDF and existing assessment/architecture/decision/audit documents; reviewed actual React map, form and request lifecycle, provider parsing, road/time interpolation, forecast lookup, exposure, ranking, API validation, budgets, signed context and production settings. The PDF remains authoritative. No routing algorithm or approved boundary interpretation was replaced.

Evidence types are separate:

- [Public baseline](evidence/pre-loom/baseline.json): real hosted empty-state measurements, six screenshots, hover instrumentation; no planning calls.
- [Public journey](evidence/pre-loom/public-smoke.json): November 1 17:55 UTC, one real plan and one corridor call, two Pelias queries. The existing smoke assertions were extended with Axe/response timing and Fit hover checks.
- [Corrected local browser](evidence/pre-loom/local-browser.json): local Vite source with captured live plan/corridor responses replayed through Playwright interception and real OpenFreeMap tiles. Clearly not a new live forecast or hosted-fix proof. One intentional error followed by successful replay. No provider calls.
- Deterministic Playwright: explicitly synthetic API data and empty test basemap, actual MapLibre rendering/source inspection. No fixtures added to production.

Raw signed contexts and provider keys are excluded from committed evidence.

## Confirmed defects and corrections

### MEDIUM: introductory card obscures map

Reproduction: open the public app with no plan, particularly at 768 or 360 px. `RouteMap.tsx` rendered `.map-empty` as an absolute-positioned white card; `styles.css` gave it fixed width, padding and a large heading. Public measurement: 280 x 211 px desktop, 250 x 268 px mobile. It visually overlapped the risk legend on phones. Its existing pointer-events rule did not prevent visual obstruction.

Correction: remove the card and its responsive CSS. `App.tsx` renders a compact `.planning-hint` in normal document flow above the map, only before a plan and outside loading/error states. The planner remains the primary action; existing status/error regions and disabled submit state remain accessible. The canvas stays free for panning/zoom. Guidance disappears after successful planning. No new modal or overlay.

### MEDIUM: Fit routes implies perpetual work before geometry exists

Reproduction: hover Fit routes on the public empty map for three seconds. It is disabled and computed cursor is `wait`. Two basemap font requests occurred, but no plan/forecast call or runtime error. Root cause: global `button:disabled { cursor: wait }` applied to a control disabled indefinitely by `!plan || !ready`. Not a hover-triggered routing calculation or MapLibre loading loop. In the actual populated public journey, hover cursor was `pointer`, enabled, with zero extra provider requests.

Correction: render Fit routes only when the map is ready and route geometry exists. Disabled controls use `not-allowed`; true running actions use `aria-busy=true` and a busy cursor. Trip submit exposes that state. Retain all-route bounds and reduced-motion behavior, add maxZoom 14 for short routes. Existing padding keeps desktop inspector space. No map recreation or provider calls on fit.

Regression coverage in `frontend/tests/browser/journey.spec.ts`: absent pre-route control, hint above canvas, six widths/no overflow, zoom/drag, delayed/error request with usable map, enabled retry through Generate routes, no guidance after success, three-second idle hover, repeated click and Enter activation, all route vertices inside viewport, unchanged selection and original map identity, no extra API calls. Local captured-response replay also exercised touch Fit.

### MEDIUM: outdated runtime security dependency; upgrade compatibility correction

`pip-audit` reported five DRF 3.16.1 advisories: PYSEC-2026-3827, PYSEC-2026-3828, CVE-2026-114138, CVE-2026-114136, CVE-2026-114137. They are not five independently reproduced application exploits. The custom bounded raw JSON parser already mitigates body-size/codec paths; AdminRenderer and TokenAuthentication are not enabled. Accept negotiation remains a DRF path; Gunicorn/proxy header limits reduce exposure but are not a substitute for patched dependencies.

Reviewed [official release notes](https://www.django-rest-framework.org/community/release-notes/#3183): 3.18.2 includes security fixes; 3.18.3 repairs a compatibility regression. Python 3.13 and Django 5.2 remain supported; removed coreapi and model/list serializer changes do not affect this database-free API. Updated only DRF to 3.18.3 and its manifest/lock constraint; no broad dependency upgrade.

The upgrade caused an existing oversized-body regression to fail: DRF now raises Django RequestDataTooBig before our parser and the custom handler returned 500. `routing/api/errors.py` now maps that exception through the existing PayloadTooLarge response, preserving structured HTTP 413 without sensitive details. Existing end-to-end oversized-body test plus new direct error-contract regression pass. [Before advisory IDs](evidence/pre-loom/python-audit-before.json); [patched runtime audit](evidence/pre-loom/python-audit-fixed.json): zero known vulnerabilities. Both frontend and backend now need deployment after approval.

## Visual and accessibility assessment

Every before/after image was opened and visually inspected at 1440x900, 1280x800, 1024x768, 768x1024, 390x844 and 360x800. All twelve corrected empty/populated states had no horizontal overflow and zero Axe WCAG A/AA violations. Keyboard autocomplete, focus visibility, slider Home/End, route selection, list alternative and reduced-motion fitting were exercised. Error-state Axe passes separately in both Playwright projects. Automation does not replace a screen-reader audit or prove all touch targets meet a particular standard; small map/attribution labels remain a usability limitation.

| Width | Public before | Local empty after | Local populated after |
|---|---|---|---|
| 1440 | [image](screenshots/pre-loom/before-1440.png) | [image](screenshots/pre-loom/after-empty-1440.png) | [image](screenshots/pre-loom/after-results-1440.png) |
| 1280 | [image](screenshots/pre-loom/before-1280.png) | [image](screenshots/pre-loom/after-empty-1280.png) | [image](screenshots/pre-loom/after-results-1280.png) |
| 1024 | [image](screenshots/pre-loom/before-1024.png) | [image](screenshots/pre-loom/after-empty-1024.png) | [image](screenshots/pre-loom/after-results-1024.png) |
| 768 | [image](screenshots/pre-loom/before-768.png) | [image](screenshots/pre-loom/after-empty-768.png) | [image](screenshots/pre-loom/after-results-768.png) |
| 390 | [image](screenshots/pre-loom/before-390.png) | [image](screenshots/pre-loom/after-empty-390.png) | [image](screenshots/pre-loom/after-results-390.png) |
| 360 | [image](screenshots/pre-loom/before-360.png) | [image](screenshots/pre-loom/after-empty-360.png) | [image](screenshots/pre-loom/after-results-360.png) |

[Loading](screenshots/pre-loom/loading-360.png), [explicit replay error](screenshots/pre-loom/error-360.png), [selected route and hour 24](screenshots/pre-loom/forecast-24.png). Screenshots may be scrolled to the map; clipped browser-page headers at the top of such captures are scroll position, not CSS clipping. Replayed result times intentionally retain the captured response and are not fresh submission timestamps.

Map remains dominant without the intro card. Desktop inspector still occupies map space by design; fit padding reserves room for it. Comparison requires scrolling on short screens. Below 1100 px the inspector moves into the document flow and tablet slider remains stacked. No further confirmed blocking layout defect was found in the inspected states; no redesign was made.

## Functional and geospatial coverage

| Area | Actual evidence | Qualification |
|---|---|---|
| Form / E02-E04 | Browser location selection, keyboard, unselected validation, delayed/error states, stale edits; timezone unit tests including DST; API finite/date/zone/load validation | Not every invalid value was manually retyped in the public UI |
| Routes / E05 | One public Fort Worth-Dallas plan: three distinct ORS driving-hgv geometries, 52,488 / 57,424.1 / 57,705.9 m, 3,520.3 / 4,044.6 / 4,192.3 s | Alternatives not guaranteed globally; no car fallback |
| Checkpoints / E06 | Public 25-mile chainage; parameterized 10/25/50, exact multiples, short/remainder/sections, endpoints and conservation in test_pipeline.py | No extra public 10/50/long-trip requests consumed |
| ETA / E07 | Nonuniform step timing/midnight tests, aware timestamps, actual public hourly intervals | Interpolation is an estimate, not traffic/break-aware dispatch timing |
| Weather | Real provenance/retrieval and ETA-valid wind/preceding-hour rain/snow; provider null/unit/batch tests | Forecast accuracy itself is not independently measured |
| Risk / E08 | Independently reviewed table expectations: wind at 25/35/45/55 = Moderate/High/Severe/No Travel at zero load; rain .10/.25/.50/1 = Moderate/High/Severe/Severe; snow .5/1/2/3 likewise; strict load equality and immediately above in test_risk.py | Shared endpoints remain documented engineering interpretations |
| Exposure / E09 | Endpoint-worst interval attribution, conserved road lengths, weighted index, unknown/No Travel tests; ranking counterexamples | Uses sampled exposure, not measured continuous hazardous miles |
| Recommendation | Severe, High, average, duration in exact lexicographic order; no rounding before comparison; incomplete/provisional/all-unsafe tests | Public weather was benign; synthetic hazardous tests are labeled |
| Map / E10 | Actual route sources, selected geometry, checkpoint inspector, pan/zoom/fit, real public tiles, WebGL fallback | No alternate browser engine/GPU hardware matrix |
| Heatmap / E11 | Public 35 cells, 49 frames, Nov 1 18:55 UTC through Nov 3 18:55 UTC; no missing frames; different wind values; slider 0/24/48 and fixed recommendation | Real categories may remain Low; categorical cells are model samples |
| API | Health/geocode/plans/corridor live journey plus serializer/provider error, timeout, budget, signature/body bounds and schema tests | Health is process-only, not provider entitlement monitoring |
| React + Django / E01 | Local suites, hosted journey and Linux Gunicorn smoke | New local changes not hosted |
| Delivery / E12-E14 | Existing published GitHub/Render deployment; new commits local | Updated release and actual Loom remain incomplete |

Weather normalization uses distinct rain plus showers, not total precipitation; snowfall is new-snow depth in cm converted to inches, not water equivalent. Missing values never become Low. Cargo remains cargo weight, not gross vehicle weight. Weather provider failures preserve unknowns and independent heatmap failure does not invalidate otherwise evaluable routes. No arbitrary score or synthetic alternative was introduced.

## Performance and lifecycle

| Measurement | Actual result | Interpretation |
|---|---|---|
| Public first browser health | 1,084 ms | Includes navigation; service cold state unknown |
| Public warm health | 317 ms | Single request, not an SLA |
| Public plan | 73,655 decoded bytes; 7,173 ms request-to-response-end | One sample, includes network |
| Public corridor | 153,229 decoded bytes; 5,628 ms | One bounded forecast dataset |
| Local page / map ready | 3,871 / 1,376 ms | Vite + real tiles + software WebGL, captured-response replay |
| Local slider label interaction | 77-314 ms for ten keyboard actions | Automation/DOM latency, not GPU-frame timing |
| Public slider label interaction | 115-577 ms | Concurrent host audit load; not reliable isolated app profiling |
| Thirty local route selections | Listeners 253 -> 253; nodes 4,253 -> 4,238; one canvas | Bounded CDP measurement after GC |
| JS heap after GC | 26,620,428 -> 27,873,848 bytes | About 1.25 MB growth; insufficient evidence of a leak or plateau |

Source listeners are installed once in the map mount effect; cleanup removes the map, markers and popup, and pending frame updates are cancelled. Tests preserve exact map identity across fits. These findings do not prove long-duration cleanup or remount stability under every scenario. MapLibre chunk remains about 1.105 MB uncompressed / 301 KB gzip plus worker; build warning remains visible. No speculative performance rewrite. A negative resource timing entry for the public worker was observed and excluded from interpretation. The 50 ms aspiration is not established and is not a PDF requirement.

## Security and reliability

Fresh focused scan covered 154 previously tracked files, 266 reachable history blobs, both configured local secret values, six downloaded public assets and seven local build artifacts; zero findings. Final staged scan covered 184 tracked files, 275 reachable history blobs and seven local build assets with zero findings, including the new receipts/screenshots. No .env is tracked. No browser Authorization/provider-token query appeared in the live journey. Public exact-origin CORS, untrusted-origin rejection, JSON preflight and HTTPS redirect passed. Malformed request returned 400; unknown path 404; no DEBUG traceback signatures. These probes do not prove every possible error response safe.

Production settings reviewed: debug off by default, stable server secret, exact CORS/no credentials, Render proxy handling, bounded parser, safe provider host/redirect rules, deadlines and per-process budgets. Context rejects compression, expires at 30 minutes and bounds encoded/decoded size and geometry. All corresponding tests pass. DRF audit issue fixed locally as described above. npm production audit: zero vulnerabilities. Full npm audit reports 12 moderate development-dependency entries, zero high/critical; the receipt is retained separately and advisories are not hidden by force-upgrading dependencies. Account-owner confirmation of old ORS-key revocation remains recorded in PRODUCTION_AUDIT.md; no new claim of direct account inspection.

## Verification ledger and failures

- Backend final: **226 passed, 0 failed, 0 skipped**.
- Frontend Vitest: **25 passed, 0 failed**.
- Full serial Playwright: **24 passed, 0 failed**; after adding error-state Axe assertions, both affected tests passed again. Tests include the original 20 cases plus two meaningful scenarios in desktop/mobile projects.
- Real Linux Gunicorn with patched DRF: **5 checks passed**.
- Ruff lint/format (backend directory, including scripts), ESLint, Prettier, TypeScript, Django checks, Python lock validation, Vite build, secret scan and whitespace checks passed.
- Deployment checks: no errors; intentional HSTS W005/W021 remain documented (no subdomain/preload policy inferred).
- Python runtime audit: before 5 advisories / one package; after upgrade 0 known vulnerabilities. npm production audit: 0.
- First focused browser run: 3 passed / 1 timed out under overlapping audit load while redundantly taking all six sizes in both projects. Removed redundant mobile size loop; retained all six desktop sizes and mobile interactions; final serial suite passed.
- First DRF-upgrade suite: 224 passed / 1 failed (oversized-body 500), fixed rather than suppressing the assertion.
- One root-directory invocation produced 225 passed / 1 failed because a subprocess expects backend cwd, and two formatting checks used the wrong config scope. Correct documented backend-directory invocations passed. No unrelated formatting/test changes were made to disguise invocation errors.

Reproduce using README backend/frontend commands; run browser suites serially. Opt-in public smoke is documented in PUBLIC_ACCEPTANCE.md; keep one plan/corridor budget per deliberate run. Do not replay captured data into the public application as if it were new live weather.

## Release status and next actions

At this audit, source fixes are committed locally after the two preserved documentation commits. No force push, history rewrite, push, cloud resource or deployment occurred. The final evidence commit will leave a clean main five commits ahead of origin/main at c87bc89; obtain actual HEAD with `git log -1` rather than embedding a self-referential commit hash here.

1. Review/authorize a normal push of the preserved documentation, UI fix, DRF/security fix and this audit. Fetch and check ancestry; run CI and verify its result.
2. Manually deploy **both** existing Render services from the approved commit: frontend needs rebuilt assets; backend needs DRF 3.18.3 and structured 413 handling. Keep Free plans/auto-deploy settings unchanged. Do not create duplicate services.
3. Verify Live SHAs, health/CORS, empty map, absent pre-route Fit, actual post-route Fit and one bounded live journey on the new deployment. Until then public defects/dependency version remain old.
4. Only after release verification, record and review the real 5-10 minute Loom and submit repository/demo/video links. No final recording was made or claimed.
