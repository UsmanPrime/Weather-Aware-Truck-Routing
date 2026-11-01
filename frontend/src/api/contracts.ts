import { z } from 'zod';

export const riskNames = [
  'low',
  'moderate',
  'high',
  'severe',
  'no_travel',
] as const;
export const riskSchema = z.enum(riskNames);
export type Risk = z.infer<typeof riskSchema>;
const nonnegative = z.number().finite().nonnegative();
const instant = z.string().datetime({ offset: true });
const position = z.tuple([
  z.number().min(-180).max(180),
  z.number().min(-90).max(90),
]);
export const placeSchema = z.object({
  id: z.string(),
  label: z.string(),
  position,
});
export type Place = z.infer<typeof placeSchema>;
export const weatherSchema = z.object({
  wind_mph: nonnegative.nullable(),
  rain_in_per_hr: nonnegative.nullable(),
  snow_in_per_hr: nonnegative.nullable(),
  source: z.literal('open_meteo'),
  data_kind: z.literal('forecast'),
  retrieved_at: instant.nullable(),
  wind_valid_at: instant.nullable(),
  precipitation_interval_start: instant.nullable(),
  precipitation_interval_end: instant.nullable(),
});
export const checkpointSchema = z.object({
  id: z.string(),
  position,
  distance_from_start_m: nonnegative,
  eta: instant,
  risk: riskSchema.nullable(),
  hazards: z.object({
    wind: riskSchema.nullable(),
    rain: riskSchema.nullable(),
    snow: riskSchema.nullable(),
  }),
  missing_fields: z.array(z.string()),
  weather: weatherSchema,
});
export type Checkpoint = z.infer<typeof checkpointSchema>;
export const routeSchema = z.object({
  id: z.string(),
  label: z.string(),
  geometry: z.object({
    type: z.literal('LineString'),
    coordinates: z.array(position).min(2),
  }),
  distance_m: nonnegative,
  duration_s: nonnegative,
  arrival_at: instant,
  checkpoints: z.array(checkpointSchema).min(2),
  segments: z.array(
    z.object({
      from_index: z.number().int(),
      to_index: z.number().int(),
      distance_m: nonnegative,
      risk: riskSchema.nullable(),
    }),
  ),
  status: z.enum(['complete', 'incomplete', 'no_travel']),
  eligible: z.boolean(),
  risk_distance_m: z.object({
    low: nonnegative,
    moderate: nonnegative,
    high: nonnegative,
    severe: nonnegative,
    no_travel: nonnegative,
  }),
  unknown_distance_m: nonnegative,
  coverage_fraction: z.number().min(0).max(1),
  average_risk_index: z.number().min(0).max(4).nullable(),
  provider_notices: z.array(
    z.object({
      code: z.string(),
      severity: z.string(),
      message: z.string().optional(),
    }),
  ),
  timing_method: z.string(),
  timing_notes: z.array(z.string()),
  provider: z.string(),
});
export type Route = z.infer<typeof routeSchema>;
const warningSchema = z.object({
  code: z.string(),
  message: z.string(),
  route_id: z.string().optional(),
});
export const planSchema = z.object({
  schema_version: z.literal('1'),
  request_id: z.string(),
  evaluated_at: instant,
  departure_at: instant,
  departure_timezone: z.string(),
  origin: placeSchema,
  destination: placeSchema,
  load_lb: nonnegative,
  checkpoint_interval_mi: z.union([
    z.literal(10),
    z.literal(25),
    z.literal(50),
  ]),
  routes: z.array(routeSchema).min(1).max(3),
  actual_route_count: z.number().int(),
  requested_route_count: z.literal(3),
  recommendation: z.object({
    route_id: z.string().nullable(),
    scope: z.enum(['all_candidates', 'available_candidates', 'none']),
    state: z.enum([
      'recommended',
      'provisional',
      'no_safe_route',
      'incomplete',
    ]),
    ordered_eligible_route_ids: z.array(z.string()),
    reasons: z.array(z.string()),
  }),
  warnings: z.array(warningSchema),
  forecast_anchor_at: instant,
  methodology_version: z.string(),
  limitations: z.array(z.string()),
  corridor_context: z.string().optional(),
});
export type Plan = z.infer<typeof planSchema>;
export interface PlanRequest {
  origin: Place;
  destination: Place;
  departure_at: string;
  departure_timezone: string;
  load_lb: number;
  checkpoint_interval_mi: 10 | 25 | 50;
}

export const corridorFrameSchema = z.object({
  valid_at: instant,
  wind_mph: z.array(nonnegative.nullable()),
  rain_in_per_hr: z.array(nonnegative.nullable()),
  snow_in_per_hr: z.array(nonnegative.nullable()),
  risk: z.array(riskSchema.nullable()),
  wind_valid_at: z.array(instant.nullable()),
  precipitation_interval_end: z.array(instant.nullable()),
  coverage_fraction: z.number().min(0).max(1),
});
export const corridorSchema = z
  .object({
    anchor_at: instant,
    load_lb: nonnegative,
    corridor_half_width_m: nonnegative,
    grid_spacing_m: nonnegative,
    cells: z
      .array(
        z.object({
          id: z.number().int(),
          position,
          polygon: z.array(position).length(5),
          model_position: position.nullable(),
          retrieved_at: instant.nullable(),
        }),
      )
      .min(1)
      .max(96),
    frames: z.array(corridorFrameSchema).length(49),
    retrieved_at: instant.nullable(),
    oldest_retrieved_at: instant.nullable(),
    source: z.literal('open_meteo'),
    data_kind: z.literal('forecast'),
    frames_with_missing_data: z.array(z.number().int()),
    generated_at: instant,
    warnings: z.array(warningSchema),
  })
  .superRefine((data, context) => {
    if (
      data.frames.some((frame) =>
        [
          frame.wind_mph,
          frame.rain_in_per_hr,
          frame.snow_in_per_hr,
          frame.risk,
          frame.wind_valid_at,
          frame.precipitation_interval_end,
        ].some((array) => array.length !== data.cells.length),
      )
    ) {
      context.addIssue({
        code: 'custom',
        message: 'Forecast arrays must align with the spatial grid.',
      });
    }
  });
export type Corridor = z.infer<typeof corridorSchema>;
export type CorridorFrame = z.infer<typeof corridorFrameSchema>;
export type WeatherMetric =
  'risk' | 'wind_mph' | 'rain_in_per_hr' | 'snow_in_per_hr';
