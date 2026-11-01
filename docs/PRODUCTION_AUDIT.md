# Production audit — November 1, 2026

Verdict: CONDITIONAL. The actual public demonstration passed; this report does not represent completion of every requested adversarial/performance investigation.

Frontend: https://spotter-weather-routing-jm1n.onrender.com

Backend: https://weather-aware-truck-routing-ddv8.onrender.com

Local and remote source baseline: 6f231075b48e810b99efa3b91cce083c26ac9865. Functional production behavior is consistent with this source, but exact Render deployment SHAs were not independently obtained. Credential rotation cannot be established from successful provider calls or absence of secrets in Git; account-side rotation evidence remains required.

## Actual public verification

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
