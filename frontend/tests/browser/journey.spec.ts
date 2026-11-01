import { test, expect } from '@playwright/test';
import { syntheticPlan, syntheticCorridor } from '../fixtures';

test.beforeEach(async ({ page }) => {
  let anchor: string | undefined;
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/health'))
      return route.fulfill({ json: { status: 'ok' } });
    if (url.pathname.endsWith('/geocode'))
      return route.fulfill({
        json: {
          places: [
            {
              id: 'synthetic-place',
              label: 'Synthetic Fort Worth, Texas',
              position: [-97.3308, 32.7555],
            },
          ],
        },
      });
    if (url.pathname.endsWith('/plans')) {
      const plan = syntheticPlan(route.request().postDataJSON());
      anchor = plan.departure_at;
      return route.fulfill({ json: plan });
    }
    if (url.pathname.endsWith('/corridor-forecasts'))
      return route.fulfill({ json: syntheticCorridor(anchor) });
    return route.fulfill({
      status: 503,
      json: { error: { message: 'Synthetic fixture endpoint unavailable.' } },
    });
  });
});

test('synthetic journey: comparison, inspector and real map sources stay synchronized', async ({
  page,
}, testInfo) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Try Fort Worth/ }).click();
  await page.getByRole('button', { name: 'Generate routes' }).click();
  await expect(
    page.getByText('Synthetic fixture data', { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Your alternatives' }),
  ).toBeVisible();
  const second = page.locator('.route-option').nth(1);
  await second.click();
  await expect(second).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('.map-shell')).toHaveAttribute(
    'data-selected-route',
    'synthetic-1',
  );
  await page.locator('.checkpoint-list button').nth(1).click();
  await expect(
    page.getByRole('complementary', { name: 'Checkpoint weather' }),
  ).toContainText('13.0');
  await expect(page.locator('.maplibregl-canvas')).toBeVisible();
  expect(
    (await page.getByTestId('route-map').boundingBox())!.height,
  ).toBeGreaterThan(300);
  await expect
    .poll(() =>
      page.getByTestId('route-map').evaluate((element) => {
        const instance = (
          element as HTMLDivElement & {
            mapInstance?: {
              queryRenderedFeatures: (options: {
                layers: string[];
              }) => unknown[];
            };
          }
        ).mapInstance;
        return (
          instance?.queryRenderedFeatures({ layers: ['selected-route'] })
            .length || 0
        );
      }),
    )
    .toBeGreaterThan(0);
  await expect
    .poll(() =>
      page.getByTestId('route-map').evaluate((element) => {
        const map = (
          element as HTMLDivElement & {
            mapInstance?: {
              getSource: (id: string) => {
                serialize: () => {
                  data: { features: { properties: { selected: boolean } }[] };
                };
              };
            };
          }
        ).mapInstance;
        return map
          ?.getSource('truck-routes')
          ?.serialize()
          .data.features.filter((f) => f.properties.selected).length;
      }),
    )
    .toBe(1);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath('journey.png'),
    fullPage: true,
  });
});

test('synthetic journey: keyboard autocomplete and validation', async ({
  page,
}) => {
  await page.goto('/');
  const origin = page.getByRole('combobox', { name: 'Origin' });
  await origin.fill('Fort Worth');
  await expect(
    page.getByRole('option', { name: 'Synthetic Fort Worth, Texas' }),
  ).toBeVisible();
  await origin.press('ArrowDown');
  await origin.press('Enter');
  await expect(origin).toHaveValue('Synthetic Fort Worth, Texas');
  await page
    .getByRole('combobox', { name: 'Destination', exact: true })
    .fill('Unselected place');
  await page.getByRole('button', { name: 'Generate routes' }).click();
  await expect(page.getByRole('alert')).toContainText('Select both locations');
});

test('synthetic journey: provider errors and changed-input state are truthful', async ({
  page,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Try Fort Worth/ }).click();
  await page.getByRole('button', { name: 'Generate routes' }).click();
  await expect(
    page.getByText('Best evaluated route', { exact: true }),
  ).toBeVisible();
  await page.getByLabel('Cargo weight').fill('40001');
  await expect(page.getByText(/Inputs changed/)).toBeVisible();
  await page.route('**/api/v1/plans', (route) =>
    route.fulfill({
      status: 503,
      json: { error: { message: 'Synthetic provider timeout.' } },
    }),
  );
  await page.getByRole('button', { name: 'Generate routes' }).click();
  await expect(page.getByRole('alert')).toContainText(
    'Synthetic provider timeout',
  );
  await expect(page.locator('.route-option')).toHaveCount(3);
});

test('synthetic corridor: 0–48 slider changes rendered weather without new requests or reranking', async ({
  page,
}) => {
  let forecastRequests = 0;
  page.on('request', (request) => {
    if (request.url().includes('/corridor-forecasts')) forecastRequests++;
  });
  await page.goto('/');
  await page.getByRole('button', { name: /Try Fort Worth/ }).click();
  await page.getByRole('button', { name: 'Generate routes' }).click();
  const slider = page.getByRole('slider', { name: 'Forecast hour' });
  await expect(slider).toBeVisible();
  await expect(slider).toHaveValue('0');
  const recommendation = await page.locator('.recommendation-note').innerText();
  await slider.focus();
  await slider.press('End');
  await expect(slider).toHaveValue('48');
  await expect(page.getByText(/Some cells are unavailable/)).toBeVisible();
  await expect
    .poll(() =>
      page.getByTestId('route-map').evaluate((element) => {
        const map = (
          element as HTMLDivElement & {
            mapInstance?: {
              queryRenderedFeatures: (options: {
                layers: string[];
              }) => { properties: { hour: number } }[];
            };
          }
        ).mapInstance;
        return map
          ?.queryRenderedFeatures({ layers: ['corridor-fill'] })
          .some((feature) => feature.properties.hour === 48);
      }),
    )
    .toBe(true);
  expect(await page.locator('.recommendation-note').innerText()).toBe(
    recommendation,
  );
  await page.getByLabel('Map layer').selectOption('wind_mph');
  await slider.focus();
  await slider.press('Home');
  await expect(slider).toHaveValue('0');
  expect(forecastRequests).toBe(1);
});
