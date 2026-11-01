import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { syntheticPlan, syntheticCorridor } from '../fixtures';

test('synthetic journey: rendered WCAG A/AA accessibility checks', async ({
  page,
}) => {
  const plan = syntheticPlan();
  await page.route('https://tiles.openfreemap.org/**', (route) =>
    route.fulfill({
      json: {
        version: 8,
        sources: {},
        layers: [
          {
            id: 'synthetic-test-background',
            type: 'background',
            paint: { 'background-color': '#e6ece9' },
          },
        ],
      },
    }),
  );
  await page.route('**/api/v1/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    return route.fulfill({
      json: path.endsWith('/plans')
        ? plan
        : path.endsWith('/corridor-forecasts')
          ? syntheticCorridor(plan.departure_at)
          : { status: 'ok' },
    });
  });
  await page.goto('/');
  await page.getByRole('button', { name: /Try Fort Worth/ }).click();
  await page.getByRole('button', { name: 'Generate routes' }).click();
  await expect(
    page.getByRole('slider', { name: 'Forecast hour' }),
  ).toBeVisible();
  const result = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(
    result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      nodes: v.nodes.map((n) => ({
        target: n.target,
        summary: n.failureSummary,
      })),
    })),
  ).toEqual([]);
});
