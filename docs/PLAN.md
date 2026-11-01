# Four-day implementation and validation plan

Current checkpoint: application implemented/tested; release configuration and local audit complete; reviewed main published with explicit authorization. Actual CI and Linux-startup evidence are in RELEASE.md. ORS driving-hgv/Pelias replace the original HERE spike in this approved sequence. Hosted verification and Loom recording remain delivery gates; cloud creation still requires separate approval.

## Precise sequence and day gates

| Day | Ordered implementation work | Exit evidence |
|---|---|---|
| 1: prove data and domain | 1. Review ambiguities D02–D13. 2. Initialize minimal React/TS/Vite and Django/DRF projects, lockfiles, environment examples and CI. 3. Spike HERE geocoding/truck routing: alternatives, notices, geometry/spans/time. 4. Spike Open-Meteo batching, units, precipitation periods and actual coverage. 5. Implement normalized types, pure risk rules, sampling, exposure and ranking with tests. 6. Deploy minimal frontend/backend preview and health check. | Genuine three-route sample for chosen demo journey; provider field mappings documented; threshold and ranking tests pass; preview connects; unresolved entitlement issues raised before polish. |
| 2: functional vertical slice | 7. Implement bounded adapters, validation, structured errors/cache/deadlines. 8. Implement plan orchestration and contract. 9. Build form, place selection, timezone/departure/load/spacing inputs. 10. Render every route, checkpoints, ETAs and summaries; synchronize selection; show recommendation reasons and unknown/No Travel states. | Browser journey from selected places to three actual alternatives and ETA-specific forecasts; deterministic API tests verify domain results; failures visible and truthful. |
| 3: corridor and polished interaction | 11. Implement signed corridor context, bounded grid and 49 forecast frames. 12. Add legend/slider/load-aware categorical weather overlay. 13. Tune map source updates, caching, geometry and payload sizes from measurements. 14. Finish responsive layouts, keyboard/list alternative, focus/contrast, loading/empty/error states. | Slider 0 and 48 work; ETA risk unchanged by slider; missing cells distinct; measured performance budgets on recorded device; accessible desktop/mobile flows. |
| 4: harden and deliver | 15. Run boundary/property/integration/browser suite and real-provider smoke checks. 16. Verify deployed CORS/HTTPS/secret configuration and failures/cold starts. 17. Resolve regressions and perform senior-review checklist. 18. Finish README, methodology/limitations, evidence and deployment instructions. 19. Publish GitHub repository and hosted URL. 20. Record and link 5–10 min Loom walkthrough. | Each ASSESSMENT matrix row has evidence; public hosted app works; clean credential scan/checks; repository/setup and Loom links verified. |

Protect day 4 for validation. At each gate prioritize 40% logic and 40% UI/performance over optional features. Do not spend assessment time on authentication, trip persistence, a custom routing engine, service orchestration, analytics dashboards or speculative abstraction. If capacity is tight, reduce cosmetic extras and optional metric toggles, while retaining all explicit PDF features. Report unmet requirements rather than hiding them.

## Test strategy

| Layer / tooling | Meaningful cases and assertions |
|---|---|
| Domain / pytest | Parameterized values below/at/above every boundary; exact load equality; decimal wind; simultaneous hazards; null/negative/nonfinite input; unit conversion. Known No Travel persists with other unknowns. |
| Geometry and ETA / pytest | Short/exact-multiple/remainder routes; no duplicated endpoints; multi-section offsets; chainage and duration conservation; timing varies by span; malformed/degenerate geometry and missing spans; coordinate order; timezone/DST/midnight. |
| Ranking / pytest | Pairwise counterexamples proving Severe beats High, High beats average, average beats time; stable ties; No Travel exclusion; incomplete candidates prevent global-best claim; distance weighting independent of checkpoint count. |
| Provider adapters / pytest + mocked HTTP | Recorded/synthetic fixtures explicitly labeled; mapping of flexible-polyline, notices, span offsets and batch order; units and intervals; null/truncated/hour-gap data; 429 Retry-After, malformed payload, deadlines/retry budget and redacted errors. No test requires external API by default. |
| API / DRF pytest | Runtime schema checks, validation/limits, status/error contract, partial response, actual alternative count, cache keys/expiry/load independence, corridor signature/expiry/body bounds; request IDs and no leaked credentials. |
| Frontend / Vitest + Testing Library | Input and timezone validation, debounce/cancellation, stale-result race, form/summary selection, risk labels/units, No Travel/unknown/provisional wording, slider frame selection without changing plan. Avoid testing library internals. |
| Browser / Playwright | Deterministic intercepted API fixtures visibly identified in test descriptions; complete three-route journey, 10/25/50 sampling, map/list selection, slider endpoints, viewport/keyboard behavior, errors/retry, WebGL fallback and stale requests. Verify rendered layer/source content, not screenshots alone. |
| Performance / browser tooling | Representative 3-route/150-checkpoint/250-cell dataset, timing for slider/source updates, payload sizes, plan/corridor timings, device/browser/network profile and cold vs warm. Record measurements; tune only demonstrated bottlenecks. |
| Live smoke / opt-in | Real credentials supplied externally; geocode → HERE truck alternatives → actual forecast → deployed browser. Verify provider notices/provenance and actual count; never assert success when unavailable. Keep separate from deterministic CI. |

Property-style assertions can be ordinary generated pytest cases without adding a property-testing dependency: increasing any weather severity never lowers combined risk; distance totals conserve; adding duplicate route shape points does not change sample count; load boundaries follow the PDF exactly. Use fixed clock injection and explicit forecast fixtures. Do not write tests that only mirror implementation expressions.

Planned CI: backend pytest and Django system/deployment checks with suitable environment; frontend typecheck, lint, Vitest and production build; Playwright against controlled test services. Pin test dependencies and browser installation. CI success is necessary but separate from real-provider and hosted verification.

## Review and evidence checklist

- Trace every explicit requirement E01–E14 to implementation and recorded check.
- Verify no API keys in code, browser bundles, logs or committed history; placeholder-only environment examples.
- Confirm all assumptions visible where they affect interpretation: exposure estimate, forecast resolution, truck profile, slider anchor, unknowns and provisional ranking.
- Check network failures, zero alternatives, fewer than three alternatives, all No Travel, missing forecast and unsupported trip horizon.
- Check model units and hourly interval handling against actual provider schema, independently of mocked fixtures.
- Preserve a concise evidence table of command/date/result, URLs, provider smoke status and known limitations. No invented test counts or performance numbers.
- README must cover prerequisites, local setup, environment variables, test commands, API contracts, architecture links, deployment, forecast/risk methodology and attribution.
- Loom outline: problem/input → three alternatives and explanation → checkpoint ETA/weather → forecast slider → load threshold example → failure/unknown state → architecture/tests/deployment and limitations. Identify any fixture-based demonstration explicitly.

## Review decisions requested

Primary policy choices: overlapping thresholds (D03), No Travel eligibility and incomplete candidates (D05), conservative interval exposure (D06), departure-anchored slider/corridor density (D08), and truck profile limitations (D11). Provider credentials, permissions and quotas remain integration prerequisites, not blockers to this completed planning deliverable.
