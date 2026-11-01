import { expect, it } from 'vitest';
import { syntheticCorridor } from '../../../tests/fixtures';
import { corridorSchema } from '../../api/contracts';
import { forecastFeatures, intensityColor } from './forecastFeatures';
import { riskColors } from '../../components/format';

it('updates exact forecast frames while preserving unknown cells and cell geometry', () => {
  const forecast = syntheticCorridor();
  const zero = forecastFeatures(forecast, 0, 'risk');
  const last = forecastFeatures(forecast, 48, 'risk');
  expect(last.features).toHaveLength(forecast.cells.length);
  expect(zero.features[0].geometry).toEqual(last.features[0].geometry);
  expect(last.features[0].properties.wind_mph).not.toBe(
    zero.features[0].properties.wind_mph,
  );
  expect(last.features[2].properties.missing).toBe(true);
  expect(last.features[2].properties.color).toBe(riskColors.unknown);
});
it.each([
  [null, 'wind_mph', riskColors.unknown],
  [55, 'wind_mph', riskColors.no_travel],
  [1, 'rain_in_per_hr', riskColors.severe],
  [1.001, 'rain_in_per_hr', riskColors.no_travel],
  [3, 'snow_in_per_hr', riskColors.severe],
  [3.001, 'snow_in_per_hr', riskColors.no_travel],
] as const)(
  'uses measured intensity thresholds without additive density',
  (value, metric, color) => {
    expect(intensityColor(value, metric, null)).toBe(color);
  },
);
it('rejects forecast arrays that do not align with spatial cells', () => {
  const data = syntheticCorridor();
  data.frames[0].wind_mph = [];
  expect(corridorSchema.safeParse(data).success).toBe(false);
});
