# Assessment analysis and acceptance criteria

Source: [fs-assessment-spotter.pdf](fs-assessment-spotter.pdf), two pages, read in full. This file transcribes its requirements and labels additional engineering decisions. Implementation progress and actual test evidence are tracked separately in IMPLEMENTATION.md.

## Explicit requirements

Build a React + Django web app helping a truck driver choose the safest route based on weather, load weight, and travel time. Third-party routing, geocoding, and weather APIs are permitted; a custom routing engine is unnecessary. Prioritize correctness and clarity over extra features.

| ID | PDF requirement / source | Planned owner | Acceptance evidence |
|---|---|---|---|
| E01 | React + Django (p1) | frontend / backend | Browser runs React; Django serves API; deployed end-to-end smoke test |
| E02 | Origin and destination input (p1) | TripForm, geocoding adapter | Both places resolved and selected; invalid/ambiguous places handled |
| E03 | Departure date/time input (p1) | TripForm, validation | Offset-aware departure survives API round trip and timezone conversion |
| E04 | Load weight input (p1) | TripForm, domain | Pounds visible; exact load boundaries tested |
| E05 | Generate 3 route options using routing API (p1) | HERE adapter | Three genuine alternatives for supported test journey; unavailable alternatives explicitly reported |
| E06 | Weather every 10 / 25 / 50 miles (p1) | checkpoint sampler | All three intervals selectable; measured chainage, endpoints and short remainder verified |
| E07 | Use truck ETA at each checkpoint (p1) | timing + forecast lookup | Different checkpoint arrival times select corresponding forecast hours |
| E08 | Calculate weather risk using provided rules (p1–2) | risk.py | Every weather/load threshold and boundary tested |
| E09 | Recommend best route balancing risk/time (p1–2) | ranking.py | Lexicographic order below, reasons displayed; unknown/No Travel decisions disclosed |
| E10 | Map all routes, checkpoints, risk levels, ETAs, route summaries (p1) | RouteMap, summaries, details | All alternatives visible; selections synchronized; each required datum inspectable |
| E11 | Corridor weather heatmap; 0–48h forecast slider (p1) | corridor sampler, ForecastControls, map layer | All alternatives' corridors covered; 49 hourly positions; legend, timestamp and missing cells visible |
| E12 | GitHub repository (p2) | delivery | Reviewable repository URL and reproducible setup |
| E13 | Hosted application (p2) | deployment | Public frontend/backend operate together without local services |
| E14 | 5–10 minute Loom walkthrough (p2) | delivery | Link and duration; demonstrates functionality and limitations |

Acceptance column operationalizes the PDF; it is not additional quoted specification. Detailed algorithm and contracts live in ARCHITECTURE.md. Four-day duration and proposed stack beyond React/Django come from the user's brief, not the PDF.

## Exact risk table (p1)

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind | <25 mph | 25–34 | 35–44 | 45–54 | ≥55 mph |
| Rain | <0.10 in/hr | 0.10–0.25 | 0.25–0.50 | 0.50–1.00 | >1.00 |
| Snow | <0.5 in/hr | 0.5–1.0 | 1.0–2.0 | 2.0–3.0 | >3.0 |

Exact load overrides (p2): wind ≥55 mph means No Travel for any load; wind 45–54 mph with load **>30,000 lb** means No Travel; wind 35–44 mph with load **>40,000 lb** means Severe. Equality at 30,000/40,000 does not trigger the corresponding override.

Exact route preference order (p2): (1) fewest Severe miles, (2) fewest High miles, (3) lowest average risk, (4) shortest travel times. Do not replace with a weighted risk/time score.

Evaluation: routes/weather/risk/recommendation 40%; UI/map/heatmap smoothness/performance 40%; code quality 15%; documentation **and walkthrough** 5%.

## Assumptions requiring review

The PDF does not define decimal wind bands, shared rain/snow endpoints, multi-hazard combination, miles attribution, average-risk encoding, No Travel eligibility, missing forecast eligibility, ETA interpolation, truck dimensions, departure horizon, corridor width, slider anchor, spatial density, performance targets, or whether every route pair can yield three alternatives. DECISIONS.md specifies proposed resolutions; none should be described as PDF mandates.

## Edge cases and acceptance scenarios

- Test values immediately below, exactly at, and immediately above every threshold, including decimal winds 34.9/44.9/54.9 and loads 30,000/40,000. Display rounding must not affect classification.
- Combine hazardous wind/rain/snow by worst severity. Missing one required variable prevents a complete safety assessment even if others are Low; a known No Travel hazard still disqualifies a route.
- Sample origin, exact interval multiples, and destination once. Short routes have two endpoints; exact multiples must not duplicate the destination. Zero-length routes and coincident endpoints are rejected.
- Conserve distance and duration across route sections, geometric interpolation, checkpoint spans and risk totals. A hazardous destination must have represented exposure under the chosen attribution rule.
- Cross midnight, timezones and daylight-saving changes using UTC instants. Resolve nonexistent/ambiguous local departure times explicitly; never silently use the browser's timezone for the origin.
- Forecast lookup must respect hourly accumulation semantics; gaps, nulls, beyond-horizon arrivals and stale responses must never become zero rain or Low risk.
- No routes, one/two alternatives, duplicate alternatives, malformed polyline, disconnected sections, unreachable places, provider restriction notices, rate limits and timeouts produce honest status and actionable errors.
- If all routes are No Travel, show no recommended departure. If any candidate is incomplete, do not claim a globally best route; show any ranking among complete candidates as provisional with the excluded candidates identified.
- Slider changes heatmap valid time only; it must not change departure, ETA-specific route risk or recommendation. New trip/load requests invalidate derived state and prevent late responses overwriting newer results.
- Heatmap missingness, loading and disabled layer are visually distinct from Low. Color is accompanied by text/legend; map details have keyboard-accessible equivalents.
- Deployment must handle HTTPS, exact CORS origins, secrets, attribution, health checks and provider failure. No live-data claim without successful provider calls.

## Completion gate

Every matrix row needs recorded evidence before final submission. Planning is approved; see IMPLEMENTATION.md for milestone evidence. The full routing workflow, deployment, repository publication and Loom remain future work.
