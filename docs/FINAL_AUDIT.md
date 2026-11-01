# Final assessment audit

Audit date: November 1, 2026. Authority: both pages of [the assessment PDF](fs-assessment-spotter.pdf). This is a critical local submission audit, not a claim of completed public delivery. No numerical assessment score or hiring outcome is inferred.

## Requirement coverage

Paths below are relative to the repository. All Python tests are under `backend/routing/tests`; browser cases are under `frontend/tests/browser`. Live receipts are separate from synthetic tests and retain their capture times.

| Requirement | Implementation | Deterministic test evidence | Live / browser evidence | Status and remaining limitation |
|---|---|---|---|---|
| E01 React + Django | `frontend/src/app/App.tsx`, `backend/config`, API views | health/client/API tests; production build | Real local React journey calls Django; desktop/mobile screenshots | Implemented locally; public end-to-end release pending |
| E02 Origin / destination | TripForm, PlaceSearch; Pelias adapter; `/geocode` | `journey.spec.ts` keyboard selection, unselected-input validation; `test_http_api.py` | `live-plan.json`: two candidates per actual search; rendered selected places | Complete locally; provider availability/quota dependent |
| E03 Departure date/time | `features/trip/time.ts`, request serializers | seven timezone cases including DST gaps/ambiguity; API offset/horizon validation | Live plan stores UTC departure; browser shows explicit IANA-zone date/time | Complete; nonexistent/ambiguous wall times require another time or UTC |
| E04 Load pounds | TripForm, pure `domain/risk.py` | `test_risk.py`: strict 30,000/40,000 equality and override boundaries; invalid input | Actual cargo field/units visible in browser | Complete; cargo is deliberately not ORS gross vehicle weight |
| E05 Three API routes | `providers/ors.py`, factory; driving-hgv | `test_ors.py`: GeoJSON, warnings, timing, duplicate rejection, long-trip truck fallback | `ors-smoke.json`, `live-plan.json`, `live-browser.json`: three distinct Fort Worth-Dallas routes | Demonstrated; public alternatives limited to 100 km and never guaranteed for arbitrary pairs |
| E06 10/25/50-mile weather checkpoints | `domain/geometry.py`, planning service | `test_pipeline.py`: spacing, short/exact/remainder, sections, endpoint uniqueness, distance conservation | Live backend proof at 10 miles; browser example at 25; all choices selectable | Complete; official step distance distributed along actual step geometry is an estimate |
| E07 Weather at truck ETA | geometry timing, `domain/forecast.py`, forecasts service | Nonuniform step timing, fallbacks, midnight, arrival-specific hourly intervals, missing coverage | Live instruction totals reconcile within rounding; checkpoint ETA/valid-time inspector | Complete; ORS durations are estimates without live traffic, stops or driver-hours scheduling |
| E08 Exact weather/load risk | `domain/risk.py`, `units.py`, `exposure.py` | Full parameterized thresholds/equality/conversions/unknowns; conservative Severe/High interval miles | Live normalized Open-Meteo units; browser hazard labels | Complete; shared PDF endpoints/decimal wind interpretations explicitly documented in D02/D03 |
| E09 Recommendation priority | `domain/ranking.py`, `services/planning.py` | Tie-breaker counterexamples; unknown/No Travel exclusion; provisional wording | Live benign weather ties resolve by duration; synthetic browser verifies hazardous/incomplete branches | Complete; no live severe-weather journey is claimed; miles and ordinal average are estimates |
| E10 All-route map / checkpoints / ETA / summaries | persistent RouteMap, RouteComparison, CheckpointInspector | Rendered source/selection checks, accessible list, WebGL fallback, synchronized details, Axe | Real tiles and geometries in screenshots; desktop/mobile browser proof | Complete locally; basemap requires network/WebGL, list remains available |
| E11 Corridor heatmap / 0-48 slider | `domain/corridor.py`, signed context/corridor service; ForecastControls/Slider; MapLibre feature-state | `test_corridor.py`, forecast features tests; rendered 0/48, one fetch, unchanged recommendation, independent failure/retry | Live 35 cells / 49 frames; different frame values, render receipts and screenshots | Complete locally; categorical center-sample cells, not continuous meteorological observations; 96-cell cap, polar/dateline bounds; 50 ms target unproven |
| E12 GitHub | public repository/main, coherent milestones, CI workflow | Lockfiles/setup/checks and history/asset secret scan | Reviewed application published at 28e8e23; Linux lockfile fix at 3b0bd5a; actual CI links in RELEASE.md | Published by authorized normal push; verify latest CI outcome via RELEASE.md and Actions |
| E13 Hosted application | `render.yaml`, Gunicorn, production settings, `DEPLOYMENT.md` | Production checks, real Linux Gunicorn startup, HTTPS/header/CORS tests, production build | Local WSL production receipt; official free-service documentation reviewed; no hosted instance | Pending separate approval/account access: actual hosted TLS, CORS, URLs/cold start must be verified |
| E14 5-10 minute Loom | `WALKTHROUGH.md` seven-to-eight-minute demonstration outline | Documentation reviewed against PDF | No recording exists | Pending manual recording and accessible real link |

## Independent correctness review

- Risk calculations retain the PDF's unusual load direction. Wind at 55 is No Travel for all loads; strict heavier-load overrides preserve equality behavior. Rain at 1.00 and snow at 3.00 remain Severe; values above become No Travel. Display rounding never enters classification.
- Road exposure sums interval lengths, not checkpoint counts. Each interval receives its worst endpoint; unknown persists unless a known No Travel hazard disqualifies it. The ordinal average is distance-weighted and has no probability interpretation. Comparison uses unrounded lexicographic values: Severe, High, average, duration.
- Official route totals remain authoritative. Geometry locations and within-instruction timing are interpolated, with explicit section fallback when timing metadata is incomplete. Duplicate geometry is removed; fewer alternatives cause truthful provisional wording, never car-route substitution.
- Forecasts are model predictions. Rain plus showers are separate liquid components; snowfall uses new-snow depth, not snow-water equivalent. Wind and precipitation valid times have distinct lookup semantics. Missing values remain missing. Forecast retrieval/cache timestamps remain exposed.
- The independent corridor uses selected slider time, while checkpoints retain truck-arrival weather. Fixed polygons and feature-state updates prevent additive density colors from manufacturing severe risk. Unknown cells are not filled by neighboring samples.
- Provider requests are bounded by coordinate batches, deadlines, transport limits, per-client throttles and conservative per-process budgets. Keys stay in server headers/environment. Signed context is uncompressed, size/geometry bounded and expires after 30 minutes. No database or speculative service infrastructure was added.
- Final screenshot review found a mobile control overlap and corrected its position. A rendered bounding-box assertion guards that defect. Accessibility checks run WCAG A/AA rules without exclusions; these automated checks do not replace a human assistive-technology audit.

## Evidence and limits by official weighting

**40% routing/weather/risk/recommendation:** deterministic backend suite plus genuine ORS/Pelias/Open-Meteo proofs cover the full pipeline. Actual warning/error branches use controlled provider fixtures; the benign live journey does not validate severe-weather forecast accuracy or certify truck dispatch suitability.

**40% UI/map/heatmap/performance:** desktop/mobile rendered journeys, real local screenshots, map synchronization, keyboard selection, independent 49-frame controls and missing/failure states are verified. Grid/payload bounds and persistent map geometry reduce work. Software-ANGLE timing samples exceed 50 ms in some frames; no p95 or hosted latency target is claimed. MapLibre's separately loaded bundle remains large and Vite reports its chunk-size warning.

**15% code quality:** pure typed domain modules, separate provider adapters/services, validated API contracts, lockfiles, meaningful tests, lint/format/type/build gates and published commits/CI. Runtime dependency audit and focused history/configured-secret/asset scan are recorded. Remaining development-tool advisories are disclosed rather than suppressed. Actual remote CI outcomes, including the first lockfile failure and normal-commit repair, are recorded in RELEASE.md.

**5% documentation and walkthrough:** current README, design decisions, requirement matrix, setup, verified screenshots, free deployment instructions and natural demonstration outline exist. A recorded Loom and actual public demo remain mandatory unfinished delivery items.

## Verification receipts

- [Machine-readable final check summary](evidence/verification.json): actual test counts, audit results and recorded check outcomes.
- [ORS proof](evidence/ors-smoke.json), [live backend plan](evidence/live-plan.json), [live corridor](evidence/live-corridor.json), [live browser](evidence/live-browser.json).
- [Secret scan](evidence/secret-scan-final.json), [runtime npm audit](evidence/npm-runtime-audit.json), [full npm audit](evidence/npm-audit.json).
- [Desktop screenshot](screenshots/desktop.png), [mobile map](screenshots/mobile.png), [mobile forecast](screenshots/mobile-forecast.png). Captures use actual local provider responses; test fixtures are never production fallback data.

No hosted/public-delivery proof is implied by local browser success. Free Render services sleep, and process-local caches/budgets reset on restart; keep a single backend process. Open-Meteo free use is noncommercial. Truck dimensions and legal dispatch restrictions are not certified. Polar/dateline corridor requests are explicitly rejected; unusually detailed geometry can exceed the bounded independent-context limit without invalidating an otherwise evaluable plan.

## Remaining release sequence

1. GitHub push approval was received and the reviewed main published. Verify latest Actions status and preserve normal history for any further release fixes; see RELEASE.md.
2. With authenticated user access, approve/create only the documented free Render services without a payment method. Verify actual Linux process startup, HTTPS health, exact CORS, a real journey and slider endpoints at both viewport sizes. Stop if a card/paid plan is required.
3. Add only verified public URLs to README, record the real 5-10 minute Loom, check its accessibility and add the link.

These are the remaining assessment-delivery blockers. The application is an assessment prototype, not certified severe-weather navigation or truck-dispatch guidance.
