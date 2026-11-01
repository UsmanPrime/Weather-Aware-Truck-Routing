# Production audit — November 1, 2026

Verdict: CONDITIONAL. The actual public demonstration passed; this report does not represent completion of every requested adversarial/performance investigation.

Frontend: https://spotter-weather-routing-jm1n.onrender.com

Backend: https://weather-aware-truck-routing-ddv8.onrender.com

Initial audit baseline: 6f231075b48e810b99efa3b91cce083c26ac9865. Current published application commit: c87bc89cfdfb39529f249fbddb2891b170d15a4e. The account owner subsequently confirmed both Render services show Live commit c87bc89 and confirmed old keys were revoked. These dashboard/account confirmations are user-reported; the agent did not independently inspect the authenticated dashboards.

## Release follow-up - November 1, 12:22-12:29 UTC

This section supersedes earlier pending-publication/tablet/security statements below. Verdict remains **CONDITIONAL for final submission**: public functionality and the tablet correction are verified; both deployment identities are now owner-confirmed; the actual Loom link remains outstanding.

**Publication:** approved commit `c87bc89cfdfb39529f249fbddb2891b170d15a4e` pushed normally after a clean preflight and compatible remote ancestry. Remote main matched that SHA. [CI run 41306283796](https://github.com/UsmanPrime/Weather-Aware-Truck-Routing/actions/runs/41306283796) completed successfully: backend and frontend jobs, including five real Linux Gunicorn checks. No backend code/configuration changed in this release. This follow-up documentation is a separate local-only change, not authorization for another push.

**Deployment identity:** the account owner reported manually deploying the frontend. Public entry JS changed from `index-Iy9gx5Wb.js` to `index-CbIwstpG.js`; CSS changed from `index-BB94Aswg.css` to `index-xlgAQcoH.css`. The latter CSS is the corrected build asset and public tablet behavior confirms it is served. In the follow-up, the owner explicitly confirmed that both frontend and backend show Live commit `c87bc89`, matching published full commit `c87bc89cfdfb39529f249fbddb2891b170d15a4e`. This closes the dashboard-confirmation action using owner-provided evidence; authenticated Render records were not independently inspected. The backend health body intentionally does not expose provider health or a release SHA.

**Credential status:** account owner explicitly confirmed old keys were revoked during this session. This is owner-reported account evidence, not independently inspected provider records. One local server-side ORS smoke request at 12:22:54 UTC succeeded with three distinct driving-hgv routes in 6.471 seconds. No key values were printed or copied into evidence. Current-key success alone does not prove old-key revocation.

### Fresh public checks and quota accounting

The extended public acceptance harness reused the existing public-smoke assertions and added Axe, response measurements and viewport checks. At 12:24 UTC the actual journey passed, but the extension failed because Axe requires an explicit browser context. This was a harness error, not an application defect. After correcting context construction, the complete extended run passed at 12:25:28 UTC. Total: two real plans, two corridor calls and one separate local ORS discovery, with no uncontrolled searches. The first extension failure is not counted as a passing full audit.

The successful run verified real Pelias autocomplete keyboard selection, destination search, exact CORS/OPTIONS and rejection of an unknown origin, HTTPS redirect, real truck routes, 25-mile chainage, ETA-specific wind and precipitation intervals, full weather coverage, recommendation explanation, map controls and 49 independent forecast frames. Routes remained 52,488 / 57,424.1 / 57,705.9 metres and 3,520.3 / 4,044.6 / 4,192.3 seconds. Corridor: 35 cells, no missing frames, +0 November 1 13:25 UTC through +48 November 3 13:25 UTC. No console/runtime/network failures or credential-bearing browser requests were recorded. Repetitive 10/25/50 submitted spacing and hazardous ranking cases remain deterministic backend/browser tests, not additional public provider calls.

### Measurements and accessibility

| Measurement | Actual result | Scope |
|---|---|---|
| First browser health, then repeat | 4,992 ms / 534 ms | Navigation-inclusive; cold state not established |
| Isolated warm health | 253 ms | One HTTPS request; no SLA inference |
| Plan response | 73,662 decoded bytes; 6,542 ms first / 1,141 ms repeat | Browser response-end timing, not provider-only time |
| Corridor response | 154,813 decoded bytes; 6,431 ms first / 1,761 ms repeat | Same caveat; repeat benefits may include caching |
| Slider displayed-label updates | 7-17 ms across ten keyboard actions | DOM/automation timing; NOT GPU frame latency |
| Public map mount to ready | 652 ms | Post-deploy browser, replayed captured responses, software WebGL; not full tile completion |
| Thirty route selections | One map canvas retained | Bounded lifecycle check; not a heap/listener leak proof |
| Public Axe | Zero WCAG A/AA violations at 1440x900, 1280x800, 768x1024, 390x844 | Both live pre-deploy and replay post-deploy states |
| Tablet slider | 132 px before; 382 px after | Public CSS regression verified |

Post-deploy verification deliberately intercepted only plan/corridor endpoints with captured real responses. It made **zero new provider calls** and is labeled replay evidence, not a new live forecast. Home/End reached 0/48; touchscreen midpoint selected hour 24 at all four widths; recommendation stayed unchanged. Visible keyboard focus and readable separated slider labels were inspected. No horizontal overflow was detected. Desktop/laptop map inspector and small supporting text remain dense; no new release-blocking layout defect was established. Axe cannot establish screen-reader usability or every focus path.

Source review confirms one mount effect creates the map/listeners; cleanup removes map, popup and markers; slider work cancels pending animation frames. Rendered source/feature-state changes are covered by deterministic Playwright. Actual production GPU latency, heap stability and exact listener counts remain unmeasured. No performance rewrite or warning-threshold increase was made.

### Security and regressions

All six post-deploy JS/CSS assets (entry, lazy map, MapLibre, worker, both styles) were fetched and hashed. No configured local ORS/Django secret or focused credential pattern was found; no localhost HTTP endpoint string was found. Scan also covered 146 tracked files and 253 reachable history blobs. Only placeholder `.env.example` files are tracked. These are scoped checks, not a guarantee against every possible credential format. Public malformed plan returned structured HTTP 400 and an unknown path returned 404 without DEBUG traceback signatures. Headers include HSTS max-age 3600, nosniff and DENY. Source/tests verify signed context expiry 1,800 seconds, encoded 128 KiB, decoded 96 KiB, maximum 6,000 coordinates and compression rejection. Actual environment values were not exposed or read from Render.

Fresh local results: **225 backend tests, 25 frontend tests, 20 browser tests passed; zero failures**. The two affected browser tests also passed separately before publication. Ruff, Ruff formatting, ESLint, Prettier, TypeScript, Django system checks, frozen Python lock check, production build and Git whitespace check passed. The known large MapLibre chunk warning remains visible. CI independently passed the same suites plus five Linux Gunicorn checks.

Evidence: [live receipt](evidence/release-verification/report.json), [explicit replay receipt](evidence/release-verification/replay-report.json), [public asset hashes](evidence/release-verification/postdeploy-assets.json), [scoped secret scan](evidence/release-verification/postdeploy-secrets.json), [post-deploy tablet screenshot](screenshots/release-verification/768.png). The screenshot directory includes all four requested sizes. Raw signed context and provider credentials are not included.

### Remaining delivery actions

1. Deployment identity action completed by owner confirmation: both existing Render services are Live at `c87bc89`. No further deployment is needed solely for this confirmation.
2. Keep auto-deploy off and plans unchanged. Frontend environment stays `VITE_API_BASE_URL=https://weather-aware-truck-routing-ddv8.onrender.com/api/v1`; backend CORS stays exactly `https://spotter-weather-routing-jm1n.onrender.com`.
3. Record and review the actual 7-9 minute Loom using WALKTHROUGH.md, hide secret-bearing tabs, verify audio/link access and add the real link. E01-E13 have implementation/public evidence with the qualifications above; E14 remains incomplete. Publish this documentation only after further approval.

---

## Earlier actual public verification

Public smoke ran at 12:08:01 UTC and 12:09:44 UTC. Both reached the supplied HTTPS URLs and passed. Each submitted one plan and one corridor request. The second run was needed to preserve screenshots after deterministic Playwright cleanup removed the first run's output. No uncontrolled corridor search or load testing occurred.

First browser health elapsed time was 4,863 ms; repeat was 548 ms. These include navigation and browser loading and are not isolated backend latency or proof of a cold start. No public page, console or network errors were recorded. Actual cross-origin browser health, exact allowed origin, rejected unknown origin, JSON POST preflight and HTTP-to-HTTPS redirect passed. Health reports process status only, not provider health.

Fort Worth-Dallas returned three distinct ORS geometries, with official normalized distances 52,488 / 57,424.1 / 57,705.9 metres and durations 3,520.3 / 4,044.6 / 4,192.3 seconds. These match historical evidence; no current route notices were returned. Pelias origin selection and destination lookup succeeded. Both live submissions used 25-mile spacing, three checkpoints per route and full reported forecast coverage. The 10/25/50 controls were exercised, but new public 10/50 submissions and a longer trip were not performed.

Checkpoint times increase along routes; endpoint chainage matches route totals. Actual wind valid times and preceding-hour precipitation intervals aligned with checkpoint ETAs. Source review of risk.py, exposure.py and forecast.py confirms mph/inches conversion, rain plus distinct showers components, new-snow depth, strict load overrides, conservative endpoint attribution, distance-weighted exposure and unknown preservation. Backend regression tests passed. This is not an independent observation of forecast accuracy or live traffic. No severe-weather fixtures were injected into production.

The real corridor contained 35 cells and 49 frames, with no missing frames. The second run covered November 1 13:09 UTC through November 3 13:09 UTC. Measurements changed between endpoints. UI slider endpoints, forecast labels, selected-route/inspector behavior and unchanged recommendation passed without additional planning requests. Public verification does not measure actual GPU frame latency, payload size, listener growth or memory leaks; the prior 50 ms target remains unproven.

## Visual and accessibility review

Actual public screenshots were inspected at 1440x900, 1280x800, 768x1024 and 390x844. Routes, checkpoint weather, units and attribution rendered. Desktop inspector occupies substantial map space; comparison/recommendation often require scrolling. Small attribution/supporting text needs human readability review. Phone map controls did not overlap in the captured state.

Confirmed MEDIUM: at 768 px, the fixed 225 px forecast label column compressed the slider track and crowded its time labels. Local CSS now stacks the track below the label from 761 through 1100 px. A deterministic rendered regression checks track width above 300 px at 768 px and captures the layout. Hosted CSS remains unchanged until separately approved publication/deployment.

Automated WCAG A/AA checks passed within the fresh deterministic desktop/mobile suite. This is not a fresh public Axe run, screen-reader audit or exhaustive keyboard/touch review. Tablet screenshot review identified a defect missed by the previous two-viewport suite.

## Security, reliability and evidence

Fresh focused scan: 137 tracked files, 239 reachable history blobs, seven build assets, two configured secret values; zero findings. Browser outgoing credential patterns and public entry-asset patterns passed. This does not establish ORS key rotation, exact deployed environment values, absence of every secret format, or absence of localhost strings in every lazy production asset.

Source review confirms debug defaults off, exact CORS origins, bounded request parsing, provider adapters and signed context limits. Context rejects compression, limits encoded/decoded sizes and geometry, and expires after 30 minutes. Actual Render environment and DEBUG error behavior need further direct verification. Do not infer them solely from source.

Confirmed LOW: public-smoke evidence originally lived under Playwright's cleaned test-results directory. Running regression tests erased public captures. The local default now uses ../.cache/public-smoke. Public audit evidence is preserved under docs/evidence/production-audit and screenshots under docs/screenshots/production-audit.

Fresh baseline: 225 backend tests, 25 frontend unit tests, 20 deterministic browser tests passed. Ruff, formatting, ESLint, TypeScript, Django checks, Python lock check and production build passed. A later overlapping pair of browser invocations caused a 19-pass/1-failure run; it is not counted as passing. The final suite is rerun serially. Temporary capture tooling also caused lint errors when left inside frontend; it was moved outside lint scope. No failure is represented as success.

## Requirement coverage

| ID | Current evidence / limitation |
|---|---|
| E01 | Public React/Django journey passed |
| E02 | Public Pelias lookup/selection passed; destination autocomplete keyboard path not separately exercised |
| E03 | Public UTC/zone serialization accepted; deterministic DST tests passed |
| E04 | Cargo input transmitted in genuine plans; strict boundaries tested locally |
| E05 | Three distinct real truck alternatives returned |
| E06 | Public 25-mile chainage verified; controls 10/25/50; remaining spacing cases tested locally |
| E07 | Actual checkpoint ETA/forecast interval alignment passed; interpolation remains estimated |
| E08 | Source review and threshold regressions passed; live weather benign |
| E09 | Recommendation explanation and stable selection passed; adversarial ranking tests local |
| E10 | Public routes/map/inspector visible; four viewport captures reviewed |
| E11 | Real 35-cell/49-frame corridor and slider independence passed; rendering performance audit incomplete |
| E12 | Published main baseline verified; new audit/fixes local only |
| E13 | Actual hosted frontend/backend journey passed; exact deployed SHAs unverified |
| E14 | Outline exists; no recorded Loom verified |

## Release recommendation and remaining work

No routing/weather blocker was observed in the bounded public demonstration. Publish the tablet/evidence fixes only after separate approval, deploy the frontend explicitly and verify the 768 px layout; do not claim local fixes are hosted. Confirm Render SHAs and ORS rotation through account evidence without exposing keys. Complete public accessibility, lazy-asset/DEBUG checks, slider profiling and controlled long-route/spacing validation before calling this a comprehensive production audit. Record the real Loom and update submission links after review.

Final isolated browser rerun: 20 passed, 0 failed; tablet regression captures visually inspected. Fresh runtime npm audit: 0 vulnerabilities; full audit: 12 moderate entries, 0 high/critical.
