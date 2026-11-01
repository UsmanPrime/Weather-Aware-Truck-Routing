/** Opt-in real-provider browser proof. Start Django/Vite locally first. No API key enters this script. */
import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';

await mkdir('../docs/screenshots', { recursive: true });
const browser = await chromium.launch({
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl'],
});
const page = await browser.newPage({
  viewport: { width: 1600, height: 1200 },
  reducedMotion: 'reduce',
});
const errors = [],
  requests = { plans: 0, corridor: 0 };
page.on('pageerror', (error) => errors.push(error.message));
page.on('request', (request) => {
  if (request.url().endsWith('/api/v1/plans')) requests.plans++;
  if (request.url().endsWith('/api/v1/corridor-forecasts')) requests.corridor++;
});
try {
  await page.goto('http://127.0.0.1:5173');
  await page.getByRole('button', { name: /Try Fort Worth/ }).click();
  const start = performance.now();
  const planResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith('/api/v1/plans') &&
      response.request().method() === 'POST',
  );
  const corridorResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith('/api/v1/corridor-forecasts') &&
      response.request().method() === 'POST',
    { timeout: 60000 },
  );
  await page.getByRole('button', { name: 'Generate routes' }).click();
  const raw = await planResponse;
  if (!raw.ok()) throw new Error(`Live plan failed with HTTP ${raw.status()}`);
  const plan = await raw.json();
  await raw.finished();
  const planMs = performance.now() - start;
  const requestMs = raw.request().timing().responseEnd;
  const forecastResponse = await corridorResponse;
  if (!forecastResponse.ok())
    throw new Error(
      `Live corridor failed with HTTP ${forecastResponse.status()}`,
    );
  const forecast = await forecastResponse.json();
  await page.getByRole('slider', { name: 'Forecast hour' }).waitFor();
  await page.waitForFunction(() => {
    const map = document.querySelector(
      '[data-testid="route-map"]',
    )?.mapInstance;
    return (
      map &&
      map.queryRenderedFeatures({ layers: ['selected-route'] }).length > 0 &&
      map.queryRenderedFeatures({ layers: ['corridor-fill'] }).length > 0
    );
  });
  const recommendation = await page.locator('.recommendation-note').innerText();
  const slider = page.getByRole('slider', { name: 'Forecast hour' });
  await slider.focus();
  await slider.press('End');
  await page.waitForFunction(() =>
    document
      .querySelector('[data-testid="route-map"]')
      .mapInstance.queryRenderedFeatures({ layers: ['corridor-fill'] })
      .some((feature) => feature.state.hour === 48),
  );
  if (
    (await page.locator('.recommendation-note').innerText()) !== recommendation
  )
    throw new Error('Slider changed recommendation');
  await slider.press('Home');
  await page.waitForFunction(
    () =>
      document
        .querySelector('[data-testid="route-map"]')
        .mapInstance.getFeatureState({ source: 'corridor-cells', id: 0 })
        .hour === 0,
  );
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: '../docs/screenshots/desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Fit routes' }).click();
  await page
    .locator('.journey-bar')
    .evaluate((element) => element.scrollIntoView({ block: 'start' }));
  await page.screenshot({ path: '../docs/screenshots/mobile.png' });
  await page.locator('.forecast-controls').scrollIntoViewIfNeeded();
  await page.screenshot({ path: '../docs/screenshots/mobile-forecast.png' });
  const measurements = [];
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator('.map-shell').scrollIntoViewIfNeeded();
  for (const hour of [12, 24, 36, 48, 0]) {
    const elapsed = await page.evaluate(async (hour) => {
      const input = document.getElementById('forecast-hour');
      const map = document.querySelector(
        '[data-testid="route-map"]',
      ).mapInstance;
      const start = performance.now();
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        'value',
      ).set.call(input, String(hour));
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      return await new Promise((resolve, reject) => {
        const tick = () => {
          if (
            map
              .queryRenderedFeatures({ layers: ['corridor-fill'] })
              .some((feature) => feature.state.hour === hour)
          )
            return resolve(performance.now() - start);
          if (performance.now() - start > 5000)
            return reject(new Error('Frame rendering deadline exceeded'));
          requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    }, hour);
    measurements.push({
      hour,
      input_to_render_ms: Math.round(elapsed * 100) / 100,
    });
  }
  const source = await page.getByTestId('route-map').evaluate((element) => {
    const map = element.mapInstance;
    return {
      route_features: map.getSource('truck-routes').serialize().data.features
        .length,
      cell_features: map.getSource('corridor-cells').serialize().data.features
        .length,
      rendered_routes: map.queryRenderedFeatures({ layers: ['route-lines'] })
        .length,
    };
  });
  const evidence = {
    run_at: new Date().toISOString(),
    data_kind: 'live_provider_browser_verification',
    browser: browser.version(),
    renderer: 'Chromium headless / software ANGLE',
    viewport: '1600×1200 and 390×844',
    route_count: plan.actual_route_count,
    checkpoint_counts: plan.routes.map((route) => route.checkpoints.length),
    routing_providers: plan.routes.map((route) => route.provider),
    grid_cells: forecast.cells.length,
    frame_count: forecast.frames.length,
    action_to_plan_ready_ms: Math.round(planMs),
    plan_http_request_ms: Math.round(requestMs),
    frame0_wind_mph: forecast.frames[0].wind_mph.slice(0, 5),
    frame48_wind_mph: forecast.frames[48].wind_mph.slice(0, 5),
    source,
    frame_render_measurements: measurements,
    requests,
    recommendation_unchanged: true,
    horizontal_overflow: await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    page_errors: errors,
    note: 'Real local backend and providers; no intercepted API responses. Five render measurements are not a general p95 guarantee.',
  };
  if (requests.plans !== 1 || requests.corridor !== 1 || errors.length)
    throw new Error('Unexpected requests or browser runtime errors');
  await writeFile(
    '../docs/evidence/live-browser.json',
    JSON.stringify(evidence, null, 2) + '\n',
  );
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  await browser.close();
}
