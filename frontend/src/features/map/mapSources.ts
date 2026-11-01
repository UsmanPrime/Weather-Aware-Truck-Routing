import type { Plan } from '../../api/contracts';
import { riskColors, routeColors } from '../../components/format';

export function routeFeatures(plan: Plan | null, selected: string | null) {
  return {
    type: 'FeatureCollection' as const,
    features:
      plan?.routes.map((route, index) => ({
        type: 'Feature' as const,
        geometry: route.geometry,
        properties: {
          route_id: route.id,
          selected: route.id === selected,
          color: routeColors[index % 3],
        },
      })) || [],
  };
}
export function checkpointFeatures(
  plan: Plan | null,
  selected: string | null,
  active: string | null,
) {
  return {
    type: 'FeatureCollection' as const,
    features:
      plan?.routes.flatMap((route) =>
        route.checkpoints.map((cp) => ({
          type: 'Feature' as const,
          geometry: { type: 'Point' as const, coordinates: cp.position },
          properties: {
            route_id: route.id,
            checkpoint_id: cp.id,
            selected: route.id === selected,
            active: cp.id === active,
            color: riskColors[cp.risk ?? 'unknown'],
          },
        })),
      ) || [],
  };
}
