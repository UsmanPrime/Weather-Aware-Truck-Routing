import { expect, it } from 'vitest';
import { syntheticPlan } from '../../tests/fixtures';
import { planSchema } from './contracts';
import { checkpointFeatures, routeFeatures } from '../features/map/mapSources';

it('validates synthetic complete plans and rejects changed wire units/shapes', () => {
  const plan = syntheticPlan();
  expect(planSchema.safeParse(plan).success).toBe(true);
  plan.routes[0].distance_m = Number.NaN;
  expect(planSchema.safeParse(plan).success).toBe(false);
});
it('builds actual map features with synchronized route and checkpoint selection', () => {
  const plan = syntheticPlan();
  const lines = routeFeatures(plan, 'synthetic-1');
  expect(lines.features).toHaveLength(3);
  expect(lines.features[1].geometry).toEqual(plan.routes[1].geometry);
  expect(lines.features.map((f) => f.properties.selected)).toEqual([
    false,
    true,
    false,
  ]);
  const points = checkpointFeatures(
    plan,
    'synthetic-1',
    plan.routes[1].checkpoints[1].id,
  );
  expect(points.features.filter((p) => p.properties.active)).toHaveLength(1);
});
