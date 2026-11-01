import type { Corridor, WeatherMetric } from '../../api/contracts';
import { riskColors } from '../../components/format';

export function intensityColor(
  value: number | null,
  metric: WeatherMetric,
  risk: keyof typeof riskColors | null,
) {
  if (metric === 'risk') return riskColors[risk ?? 'unknown'];
  if (value === null) return riskColors.unknown;
  if (metric === 'wind_mph')
    return value >= 55
      ? riskColors.no_travel
      : value >= 45
        ? riskColors.severe
        : value >= 35
          ? riskColors.high
          : value >= 25
            ? riskColors.moderate
            : riskColors.low;
  const [low, high, severe, noTravel] =
    metric === 'rain_in_per_hr' ? [0.1, 0.25, 0.5, 1] : [0.5, 1, 2, 3];
  return value > noTravel
    ? riskColors.no_travel
    : value >= severe
      ? riskColors.severe
      : value >= high
        ? riskColors.high
        : value >= low
          ? riskColors.moderate
          : riskColors.low;
}
export function forecastFeatures(
  forecast: Corridor | null,
  hour: number,
  metric: WeatherMetric,
) {
  const frame = forecast?.frames[hour];
  return {
    type: 'FeatureCollection' as const,
    features:
      forecast && frame
        ? forecast.cells.map((cell, index) => {
            const risk = frame.risk[index];
            const value = metric === 'risk' ? null : frame[metric][index];
            return {
              type: 'Feature' as const,
              geometry: {
                type: 'Polygon' as const,
                coordinates: [cell.polygon],
              },
              properties: {
                cell_id: cell.id,
                hour,
                valid_at: frame.valid_at,
                wind_valid_at: frame.wind_valid_at[index],
                precipitation_interval_end:
                  frame.precipitation_interval_end[index],
                risk,
                wind_mph: frame.wind_mph[index],
                rain_in_per_hr: frame.rain_in_per_hr[index],
                snow_in_per_hr: frame.snow_in_per_hr[index],
                missing: metric === 'risk' ? risk === null : value === null,
                color: intensityColor(value, metric, risk),
              },
            };
          })
        : [],
  };
}
