# Evaluation methodology

The [assessment rules](ASSESSMENT.md) are authoritative. Boundary interpretations and conservative choices below are engineering assumptions, recorded in [DECISIONS.md](DECISIONS.md), not additional PDF requirements.

## Road sampling and ETA

ORS returns truck geometry, official distance/duration and instruction geometry indices. Step totals are reconciled to section and route totals to absorb provider rounding. Within each step, official distance and time are distributed by geometric edge length. Missing/incomplete step timing triggers a disclosed section-level approximation. Distances are not straight-line endpoint distances.

Sample the origin, each selected 10/25/50-mile chainage and destination exactly once, including a short final remainder. Distances/times conserve official totals. Arrival is departure plus cumulative estimated travel seconds. Dates are aware and evaluated in UTC; the selected IANA zone controls entry/display. ETAs do not include live traffic, breaks or driver-hours constraints.

## Forecast selection and units

Open-Meteo provides hourly UTC model forecasts. Wind at 10 m uses the nearest available timestamp within 30 minutes, ties earlier, with no horizon extrapolation. Rain/showers and snowfall use the preceding-hour interval `(start, end]` containing the ETA. Rain plus showers are distinct large-scale/convective liquid components; total precipitation is not added. Snowfall is new-snow depth, not snow-water equivalent or accumulated ground depth.

Normalize km/h to mph, liquid mm to inches/hour and snowfall cm to inches/hour. Preserve retrieval/source/valid-time metadata and null measurements. Missing weather remains unknown, except a known No Travel hazard still disqualifies travel.

## Risk and cargo rules

| Hazard | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind mph | <25 | [25,35) | [35,45) | [45,55) | >=55 |
| Rain in/hr | <0.10 | [0.10,0.25) | [0.25,0.50) | [0.50,1.00] | >1.00 |
| Snow in/hr | <0.5 | [0.5,1.0) | [1.0,2.0) | [2.0,3.0] | >3.0 |

Cargo >30,000 lb with wind [45,55) means No Travel. Cargo >40,000 lb with wind [35,45) means Severe. Equality at either load boundary does not trigger that override. Wind >=55 means No Travel for every load. Take the worst applicable hazard after overrides. Cargo is not automatically passed to ORS as gross vehicle weight.

## Exposure and recommendation

Each interval receives the worse endpoint risk; an unknown endpoint makes the interval unknown unless a known endpoint prohibits travel. Sum interval road lengths by category, rather than counting checkpoints. Coverage measures intervals with complete endpoint measurements. Average risk uses distance-weighted ordinal values Low=0 through No Travel=4 and is unavailable for incomplete evaluation; it is not a probability.

Exclude No Travel and incomplete routes from definitive recommendations. Compare complete eligible routes lexicographically: Severe distance, High distance, average risk, then duration, using unrounded values. Stable provider order breaks exact ties. Missing alternatives/unevaluated competitors make a selection provisional; all unsafe or incomplete candidates produce no safe evaluated recommendation. Exposure remains a sampled conservative estimate.

## Independent corridor forecast

Sample a bounded grid around the union of alternatives, extending 25 km either side. Start at 12 km spacing and adapt to at most 96 cells. Frame 0 is departure; frame 48 is 48 hours later. Reuse cached forecast series and preload all 49 frames. Checkpoint weather always remains tied to ETA.

Cells show model measurements at sample locations, not continuous observations. Categorical colors do not density-blend Low cells into Severe. Missing cells/frames remain explicit. Later frames may exceed actual forecast coverage without invalidating an otherwise complete route evaluation. Polar/dateline corridors are rejected; very detailed routes can exceed signed-context limits independently of route planning.
