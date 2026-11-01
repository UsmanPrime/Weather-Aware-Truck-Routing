/** Synthetic responses exclusively for intercepted browser/unit tests. Never imported by the app. */
import {
  planSchema,
  corridorSchema,
  type PlanRequest,
} from '../src/api/contracts';

export function syntheticPlan(input?: PlanRequest) {
  const departure =
    input?.departure_at || new Date(Date.now() + 3600000).toISOString();
  const zone = input?.departure_timezone || 'America/Chicago';
  const spacing = (input?.checkpoint_interval_mi || 25) * 1609.344;
  const routes = [52488, 57424, 57706].map((distance, index) => {
    const seconds = [3520, 4045, 4192][index];
    const chainages = [0];
    for (let n = spacing; n < distance; n += spacing) chainages.push(n);
    chainages.push(distance);
    const coordinates: [number, number][] = [
      [-97.3308, 32.7555],
      [-97.1, 32.73 + index * 0.07],
      [-96.797, 32.7767],
    ];
    const cps = chainages.map((m, i) => ({
      id: `synthetic-${index}-cp-${i}`,
      position:
        i === 0
          ? coordinates[0]
          : i === chainages.length - 1
            ? coordinates[2]
            : coordinates[1],
      distance_from_start_m: m,
      eta: new Date(
        Date.parse(departure) + ((seconds * m) / distance) * 1000,
      ).toISOString(),
      risk: 'low',
      hazards: { wind: 'low', rain: 'low', snow: 'low' },
      missing_fields: [],
      weather: {
        wind_mph: 12 + index,
        rain_in_per_hr: 0,
        snow_in_per_hr: 0,
        source: 'open_meteo',
        data_kind: 'forecast',
        retrieved_at: departure,
        wind_valid_at: departure,
        precipitation_interval_start: new Date(
          Date.parse(departure) - 3600000,
        ).toISOString(),
        precipitation_interval_end: departure,
      },
    }));
    return {
      id: `synthetic-${index}`,
      label: `Route ${index + 1}`,
      geometry: { type: 'LineString', coordinates },
      distance_m: distance,
      duration_s: seconds,
      arrival_at: new Date(
        Date.parse(departure) + seconds * 1000,
      ).toISOString(),
      checkpoints: cps,
      segments: chainages.slice(1).map((m, i) => ({
        from_index: i,
        to_index: i + 1,
        distance_m: m - chainages[i],
        risk: 'low',
      })),
      risk_distance_m: {
        low: distance,
        moderate: 0,
        high: 0,
        severe: 0,
        no_travel: 0,
      },
      unknown_distance_m: 0,
      coverage_fraction: 1,
      average_risk_index: 0,
      eligible: true,
      status: 'complete',
      provider: 'ors',
      provider_notices: [],
      timing_method: 'instruction_step_interpolation',
      timing_notes: ['Synthetic fixture timing — automated test only.'],
    };
  });
  return planSchema.parse({
    corridor_context: 'synthetic-corridor-context',
    schema_version: '1',
    request_id: 'synthetic-plan',
    evaluated_at: departure,
    departure_at: departure,
    departure_timezone: zone,
    origin: input?.origin || {
      id: 'a',
      label: 'Synthetic Fort Worth',
      position: [-97.3308, 32.7555],
    },
    destination: input?.destination || {
      id: 'b',
      label: 'Synthetic Dallas',
      position: [-96.797, 32.7767],
    },
    load_lb: input?.load_lb ?? 30000,
    checkpoint_interval_mi: input?.checkpoint_interval_mi || 25,
    requested_route_count: 3,
    actual_route_count: 3,
    routes,
    recommendation: {
      route_id: 'synthetic-0',
      scope: 'all_candidates',
      state: 'recommended',
      ordered_eligible_route_ids: routes.map((r) => r.id),
      reasons: [
        'Synthetic fixture: shortest estimated time after identical risk exposure.',
      ],
    },
    warnings: [
      {
        code: 'synthetic_test_data',
        message:
          'Synthetic fixture data — automated test only. Not live weather or routing.',
      },
    ],
    forecast_anchor_at: departure,
    methodology_version: 'synthetic-test',
    limitations: ['Synthetic test fixture.'],
  });
}

export function syntheticCorridor(
  anchor = new Date(Date.now() + 3600000).toISOString(),
) {
  const cells = [0, 1, 2].map((i) => {
    const x = -97.2 + i * 0.12,
      y = 32.77;
    return {
      id: i,
      position: [x, y],
      polygon: [
        [x - 0.06, y - 0.05],
        [x + 0.06, y - 0.05],
        [x + 0.06, y + 0.05],
        [x - 0.06, y + 0.05],
        [x - 0.06, y - 0.05],
      ],
      model_position: [x, y],
      retrieved_at: anchor,
    };
  });
  const frames = Array.from({ length: 49 }, (_, i) => {
    const at = new Date(Date.parse(anchor) + i * 3600000).toISOString();
    const wind = [10 + i * 0.5, 15 + i * 0.7, i === 48 ? null : 22 + i * 0.8];
    return {
      valid_at: at,
      wind_mph: wind,
      rain_in_per_hr: [0, 0, i === 48 ? null : 0],
      snow_in_per_hr: [0, 0, i === 48 ? null : 0],
      risk: wind.map((value) =>
        value === null
          ? null
          : value >= 55
            ? 'no_travel'
            : value >= 45
              ? 'severe'
              : value >= 35
                ? 'high'
                : value >= 25
                  ? 'moderate'
                  : 'low',
      ),
      wind_valid_at: [at, at, i === 48 ? null : at],
      precipitation_interval_end: [at, at, i === 48 ? null : at],
      coverage_fraction: i === 48 ? 2 / 3 : 1,
    };
  });
  return corridorSchema.parse({
    anchor_at: anchor,
    load_lb: 30000,
    corridor_half_width_m: 25000,
    grid_spacing_m: 12000,
    cells,
    frames,
    retrieved_at: anchor,
    oldest_retrieved_at: anchor,
    source: 'open_meteo',
    data_kind: 'forecast',
    frames_with_missing_data: [48],
    generated_at: anchor,
    warnings: [
      {
        code: 'synthetic_test_data',
        message: 'Synthetic corridor fixture — automated test only.',
      },
    ],
  });
}
