# Milestone 1 implementation evidence

## Subsequent phase 1 — ORS migration (November 1)

The ORS key was found in the modified tracked template rather than .env; configuration was moved into ignored backend/.env and the template scrubbed before staging. No value was printed. Native GeoJSON driving-hgv and Pelias adapters now share normalized types with the retained optional HERE adapter. Structured timeout/quota errors, coordinate/step validation and exact-geometry deduplication are tested.

Live Fort Worth–Dallas requests returned three distinct truck geometries twice: official lengths 52,488.0 / 57,424.1 / 57,705.9 m, durations 3,520.3 / 4,044.6 / 4,192.3 s. No route warnings. Step ranges cover each route; step distance rounding differs by at most 0.2 m and duration sums agree within floating-point precision. [Adapter smoke evidence](evidence/ors-smoke.json). A first adapter attempt failed content negotiation; sending `Accept: application/geo+json` corrected it. Five routing requests total during initial proof (two success, three failed); no broad corridor search needed. No traffic-aware ETA claim.

Phase 1 deterministic tests: 165 passed; Django checks 0 issues. Lint/format verified before the phase commit. Caching and request-budget enforcement follow in the service pipeline.

Assessment window: November 1–4, 2026. Milestone work and checks below performed November 1. This is an implementation status report, not a claim that the full assessment is complete. The approved architecture has been preserved with the user's targeted corrections.

## Implemented scope

- React 19 / TypeScript / Vite application with Tailwind design tokens, honest service-status UI, validated health response and lazy MapLibre boundary. MapLibre is installed but no map, route form or heatmap is presented as working.
- Database-free Django 5.2 / DRF project and `GET /api/v1/health`. Structured provider/DRF errors; no authentication, database, Redis, Celery or analytics installed/configured.
- Frozen domain data structures, explicit units, normalization, all PDF weather/load thresholds, unknown-preserving combination and lexicographic eligible-route ordering. Ranking consumes validated comparison metrics; route exposure aggregation is future work.
- Independently injectable HERE and Open-Meteo adapters, bounded JSON transport, response validation, credential-safe errors, redirects refused, provider protocols and opt-in smoke command.
- Dependency manifests/locks, Ruff/Prettier/ESLint, pytest/Vitest, environment templates, local commands and minimal GitHub Actions workflow. CI is configured but has not run remotely because nothing has been pushed.

## Architecture corrections applied

1. D13 now gates route evaluation on checkpoint ETA forecast coverage alone. Independent missing heatmap frames remain unknown. A regression test demonstrates usable ETA weather even when +48 hours is unavailable.
2. HERE span duration/length are metadata, not speed-based splitting attributes. The request includes `dynamicSpeedInfo`; normalized section summary and travel-summary durations remain distinct. No checkpoint ETA interpolation is implemented or claimed accurate yet.
3. Open-Meteo normalizes separate hourly rain + showers components once; total precipitation is not added. Snowfall uses cm of new snowfall, never snow-water equivalent or snow depth on the ground. Actual response units/UTC timestamps are validated. Preceding-hour accumulation boundaries and separate wind sampling are explicit and tested.
4. Batches are capped at 25 coordinates; a real three-coordinate request measured 16,566 response bytes. Corridor optimization remains measurement-led future work.
5. Signed corridor context is not implemented in this milestone. The approved contract now starts uncompressed and rejects compressed tokens, with explicit encoded/decoded size, route/point count, coordinate and expiry bounds. Compression would require a streaming decompression limit before parsing.
6. PDF thresholds/load rules remain unchanged. D02/D03 continue documenting decimal wind and ambiguous shared rain/snow boundaries; tests cover immediately below/at/above each boundary and exact load equality.

## Provider proof: real calls versus fixtures

[Sanitized live report](evidence/provider-smoke.json), captured at 07:02 UTC on November 1, 2026:

| Provider | Actual outcome | Evidence / limits |
|---|---|---|
| Open-Meteo | Live success | Three representative I-55 coordinates (Chicago, Bloomington IL, St Louis); returned grid coordinates match request order within validation tolerance; 168 hours each, November 1 00:00 UTC through November 7 23:00 UTC; zero missing required normalized measurements; all 49 positions from November 1 08:00 UTC through +48 hours available at every location. 1.033 s request/parse measurement; 16,566 raw JSON bytes. This one measurement is not a p95 performance claim. |
| HERE Routing v8 | Blocked before HTTP | Server environment has no HERE_API_KEY. No truck entitlement, route count, actual alternative geometry, notices, spans or timing reconciliation has been live-verified. The command stops credential-less retries; the other corridors have not been called. |

The combined smoke command deliberately exits **1** because HERE is blocked even though weather succeeded. Weather coordinates are representative corridor samples, not checkpoints from a live HERE route. Do not present the report as an end-to-end routing proof. Synthetic unit fixtures are confined to tests and identified as synthetic; they are not used by production adapters or smoke commands.

HERE's live proof command is ready to try Chicago–Indianapolis, Dallas–Houston and Atlanta–Nashville when credentials exist, stopping after three distinct exact decoded geometries are found. It records actual and duplicate counts, official distances/durations, section/travel summaries, span offsets/totals and notices. Exact-geometry deduplication is implemented; near-equivalent alternatives are not yet compared geometrically.

Official semantics checked against [HERE spans](https://docs.here.com/routing/docs/routing-v8-span), [HERE section summaries](https://docs.here.com/routing/docs/routing-v8-route-summary), and [Open-Meteo hourly documentation](https://open-meteo.com/en/docs). Documentation establishes parameter semantics; it does not replace missing live HERE evidence or prove physical forecast accuracy.

## Executed verification

Environment: Windows, Node 24.11.0, Python 3.13.17. Django checks/tests ran with `DJANGO_DEBUG=true`, no database, no HERE credentials. Commands below run from their respective app directories with dependency locks; local `.env` usage is in README.

| Check | Observed result |
|---|---|
| Backend `uv run pytest` | **151 passed, 0 failed** (latest full run 0.40 s). Includes threshold/strict-load boundaries, invalid/overflow measurements, conversions, hazard combination, ranking, adapter schemas/units/batch ordering, accumulation lookup, decoder vectors/truncation, notices, transport errors/redaction, health and independent ETA coverage. |
| `uv run python manage.py check` | **0 issues**, 0 silenced. |
| `uv run ruff check .`, `uv run ruff format --check .` | Both passed; 31 Python files formatted. |
| Frontend `npm test` | **5 passed, 0 failed**, Vitest 5.0.5. Synthetic HTTP contract success, status failure and three malformed payloads. |
| `npm run lint`, `npm run typecheck` | Both passed. |
| `npm run format:check` | Passed. |
| `npm run build` | Passed, Vite 7.3.7. JS 224.04 kB / gzip 70.06 kB; CSS 8.65 kB / gzip 2.51 kB. Map engine not eagerly bundled into the health shell. |
| [Real local HTTP smoke](evidence/local-http-smoke.json) | **3/3 checks passed**: Django health, Vite HTML, proxied health. Processes stopped afterward. This is not a rendered-browser or Playwright test. |
| Live provider smoke | **1 provider successful, 1 blocked**, separate from pytest; see above. |
| [Runtime npm audit](evidence/npm-runtime-audit.json) | Zero reported vulnerabilities after MapLibre update. |
| [Full npm audit](evidence/npm-audit.json) | Exit 1: 12 moderate affected dependency entries, 0 high/critical. Current remaining root advisory concerns minimatch <11.0.1 through development lint tooling. No unsupported transitive major override applied. |
| [Staged source secret scan](evidence/secret-scan.json) | 64 staged text files checked; 0 findings for private keys, AWS/GitHub tokens, quoted credential assignments and authenticated URLs. Binary assessment PDF excluded; known synthetic URL in the redaction test allowlisted. Focused scan, not an exhaustive secret-detection guarantee. Environment/cache/build artifacts excluded by .gitignore. |
| Lockfile / staged whitespace checks | `uv lock --check --offline` passed; npm lock metadata refreshed successfully with declared Node minimum; `git diff --cached --check` passed. |

During verification, initial lint/format issues were corrected. A first local HTTP smoke used the wrong Vite working directory and failed with 404; corrected working directory produced the recorded 3/3 success. Initial MapLibre 5 and Vitest 3 selections were replaced with patched MapLibre 6.16 and Vitest 5 releases; supported ESLint 10 tooling replaced deprecated ESLint 9. This report uses final results, not those initial failures as successes.

## Remaining technical risks and next milestone

- HERE live entitlement, actual alternatives and timing granularity are unresolved. Supply HERE_API_KEY in the server environment/untracked .env and rerun the proof before ETA work. No need to expose the key in chat or frontend.
- Summary duration can include pre/post actions while travel-summary duration excludes them. Resolve this allocation, validate span sums and geometry chainage, and label interpolation error before generating checkpoint ETAs. No routing/sampling accuracy claim yet.
- Provider proofs have an 8-second transport timeout and 5 MiB response bound. End-to-end deadlines, retry budget, bounded orchestration/cache/throttling and trip validation are not implemented yet.
- Batch location mapping checks response order with a one-degree grid tolerance. Nearby swapped coordinates could evade that guard; the live proof uses well-separated locations. Retain order semantics and verify close-coordinate behavior before route integration.
- Development-only audit findings remain as recorded. CI and browser interaction/visual checks have not run remotely. No deployment or hosted performance evidence exists.
- Stable production secret and production security/CORS settings are prerequisites for deployment and signed context. Missing secret with debug disabled now fails startup explicitly.

Next milestone: close HERE live verification, implement tested geometry/chainage and provider-supported ETA estimation, distance-weighted exposure and recommendation explanations, then expose validated `/geocode` and `/plans` endpoints and the React input → all-routes map/list vertical slice. Retain explicit unknown/provisional/No Travel states. Independent corridor heatmap follows that complete routing slice.

Git origin fetch/push configuration is `https://github.com/UsmanPrime/Weather-Aware-Truck-Routing.git`; a read-only remote-ref request succeeded. The local milestone commit is reported at completion; no push or deployment is authorized or performed.
