/** Opt-in acceptance against supplied real URLs. One plan/corridor; no fixtures or retries. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { chromium, expect } from '@playwright/test';

const local = process.argv.includes('--allow-localhost');
const requireThree = process.argv.includes('--require-three');
function origin(value, name) {
  assert(value, `Set ${name} to the actual deployed origin.`);
  const url = new URL(value);
  assert(
    !url.username &&
      !url.password &&
      !url.search &&
      !url.hash &&
      url.pathname === '/',
    `${name} must be a plain origin without credentials, query or path.`,
  );
  assert(
    url.protocol === 'https:' ||
      (local &&
        ['localhost', '127.0.0.1'].includes(url.hostname) &&
        url.protocol === 'http:'),
    `${name} must use HTTPS; loopback HTTP needs --allow-localhost.`,
  );
  return url.origin;
}
const frontend = origin(process.env.PUBLIC_FRONTEND_URL, 'PUBLIC_FRONTEND_URL');
const backend = origin(process.env.PUBLIC_BACKEND_URL, 'PUBLIC_BACKEND_URL');
const api = `${backend}/api/v1`;
const output = process.env.PUBLIC_SMOKE_OUTPUT || '../.cache/public-smoke';
await mkdir(output, { recursive: true });
const report = {
  run_at: new Date().toISOString(),
  frontend,
  backend,
  mode: local ? 'local rehearsal' : 'public real-provider acceptance',
  checks: [],
  warnings: [],
  errors: [],
  requests: { plans: 0, corridor: 0 },
  console_errors: [],
  network_errors: [],
};
const browser = await chromium.launch({
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl'],
});
const page = await browser.newPage({
  viewport: { width: 1440, height: 1100 },
  reducedMotion: 'reduce',
});
page.setDefaultTimeout(30000);
const check = (name) => report.checks.push(name);
const safePath = (value) => {
  const url = new URL(value);
  return `${url.origin}${url.pathname}`;
};
const credentialPattern =
  /(?:-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{30,}|\bAKIA[A-Z0-9]{16}\b|(?:ORS_API_KEY|HERE_API_KEY|DJANGO_SECRET_KEY)\s*[=:]\s*["'][A-Za-z0-9_./+-]{16,}["'])/;
const firstHealth = page.waitForResponse(
  (response) => response.url() === `${api}/health`,
  { timeout: 120000 },
);
page.on('pageerror', () =>
  report.errors.push(
    'Browser runtime error (details omitted to avoid sensitive payloads).',
  ),
);
page.on('console', (message) => {
  if (message.type() === 'error')
    report.console_errors.push(
      'Console error; inspect browser locally (payload omitted).',
    );
});
page.on('request', (request) => {
  const url = new URL(request.url());
  if (url.pathname === '/api/v1/plans' && request.method() === 'POST')
    report.requests.plans++;
  if (
    url.pathname === '/api/v1/corridor-forecasts' &&
    request.method() === 'POST'
  )
    report.requests.corridor++;
  if (
    url.username ||
    url.password ||
    [...url.searchParams.keys()].some((key) =>
      /^(apikey|api_key|access_token|token)$/i.test(key),
    ) ||
    request.headers().authorization
  )
    report.errors.push(
      `Credential-bearing browser request: ${safePath(request.url())}`,
    );
});
page.on('requestfailed', (request) => {
  if (request.failure()?.errorText !== 'net::ERR_ABORTED')
    report.network_errors.push(safePath(request.url()));
});
page.on('response', (response) => {
  if (response.status() >= 400)
    report.network_errors.push(
      `${response.status()} ${safePath(response.url())}`,
    );
});
try {
  const start = performance.now();
  const document = await page.goto(frontend, {
    waitUntil: 'domcontentloaded',
    timeout: 120000,
  });
  assert(document?.ok(), 'Frontend document failed.');
  const health = await firstHealth;
  report.first_health_ms = Math.round(performance.now() - start);
  report.first_health_status = health.status();
  assert(
    health.ok() && (await health.json()).status === 'ok',
    'First health failed (possible cold-start loading response); wait for wake-up and rerun manually.',
  );
  await expect(
    page.getByRole('heading', { name: 'Plan your route' }),
  ).toBeVisible();
  check('frontend and first real browser health response');
  if (!local) {
    assert(
      health.headers()['access-control-allow-origin'] === frontend,
      'Exact frontend CORS origin missing.',
    );
    const redirect = await page.request.get(
      `${backend.replace('https:', 'http:')}/api/v1/health`,
      { maxRedirects: 0, timeout: 90000 },
    );
    assert(
      [301, 302, 307, 308].includes(redirect.status()) &&
        redirect.headers().location?.startsWith('https://'),
      'Public HTTP did not redirect to HTTPS.',
    );
    const blocked = await page.request.get(`${api}/health`, {
      headers: { Origin: 'https://untrusted.example.test' },
    });
    assert(
      !blocked.headers()['access-control-allow-origin'],
      'Untrusted origin was allowed.',
    );
    const preflight = await page.request.fetch(`${api}/plans`, {
      method: 'OPTIONS',
      headers: {
        Origin: frontend,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
      },
    });
    assert(
      preflight.ok() &&
        preflight.headers()['access-control-allow-origin'] === frontend,
      'Public JSON POST preflight failed.',
    );
    check(
      'public HTTPS redirect, exact CORS, rejected origin and JSON preflight',
    );
  } else
    report.warnings.push(
      'Local rehearsal cannot verify public TLS or production origin configuration.',
    );

  const search = page.waitForResponse((response) =>
    response.url().startsWith(`${api}/geocode?`),
  );
  await page
    .getByRole('combobox', { name: 'Origin', exact: true })
    .fill('Fort Worth');
  const places = await search;
  assert(
    places.ok() && (await places.json()).places.length > 0,
    'Live Pelias search failed.',
  );
  await page.getByRole('option').first().click();
  const destination = await page.request.get(`${api}/geocode?q=Dallas`);
  assert(
    destination.ok() && (await destination.json()).places.length > 0,
    'Live destination search failed.',
  );
  check('live Pelias origin selection and destination lookup');
  await page.getByRole('button', { name: /Try Fort Worth/ }).click();
  const interval = page.getByLabel('Weather sampling');
  for (const value of ['10', '50', '25']) {
    await interval.selectOption(value);
    await expect(interval).toHaveValue(value);
  }
  check('10/25/50-mile controls; one actual 25-mile plan');
  const planResponse = page.waitForResponse(
    (response) =>
      response.url() === `${api}/plans` &&
      response.request().method() === 'POST',
    { timeout: 100000 },
  );
  const corridorResponse = page.waitForResponse(
    (response) =>
      response.url() === `${api}/corridor-forecasts` &&
      response.request().method() === 'POST',
    { timeout: 130000 },
  );
  await page.getByRole('button', { name: 'Generate routes' }).click();
  const rawPlan = await planResponse;
  assert(rawPlan.ok(), `Live planning failed: HTTP ${rawPlan.status()}.`);
  const plan = await rawPlan.json();
  assert(
    plan.routes.length >= 1 &&
      plan.routes.length <= 3 &&
      plan.actual_route_count === plan.routes.length,
  );
  if (requireThree)
    assert.equal(
      plan.routes.length,
      3,
      'Strict demonstration requires three genuine alternatives.',
    );
  else if (plan.routes.length !== 3)
    report.warnings.push(
      `Only ${plan.routes.length} genuine truck alternatives returned; no substitution permitted.`,
    );
  const shapes = plan.routes.map((route) =>
    createHash('sha256')
      .update(JSON.stringify(route.geometry.coordinates))
      .digest('hex'),
  );
  assert(
    plan.routes.some((route) =>
      route.checkpoints.some(
        (cp) =>
          cp.weather.retrieved_at &&
          cp.weather.wind_valid_at &&
          cp.weather.wind_mph !== null,
      ),
    ),
    'No usable live ETA weather was returned.',
  );
  assert.equal(
    new Set(shapes).size,
    plan.routes.length,
    'Duplicate geometry returned.',
  );
  for (const route of plan.routes) {
    assert(
      route.provider === 'ors' &&
        route.distance_m > 0 &&
        route.duration_s > 0 &&
        route.geometry.coordinates.length > 2,
    );
    assert(route.checkpoints.length >= 2);
    route.checkpoints
      .slice(1, -1)
      .forEach((cp, index) =>
        assert(
          Math.abs(cp.distance_from_start_m - (index + 1) * 25 * 1609.344) <
            0.01,
        ),
      );
    assert(
      Math.abs(
        route.checkpoints.at(-1).distance_from_start_m - route.distance_m,
      ) < 0.01,
    );
    assert(
      route.checkpoints
        .slice(1)
        .every(
          (cp, index) =>
            Date.parse(cp.eta) > Date.parse(route.checkpoints[index].eta),
        ),
    );
    for (const cp of route.checkpoints) {
      assert(
        cp.weather.source === 'open_meteo' &&
          cp.weather.data_kind === 'forecast',
      );
      if (cp.weather.wind_valid_at)
        assert(
          Math.abs(Date.parse(cp.weather.wind_valid_at) - Date.parse(cp.eta)) <=
            1800000,
        );
      if (cp.weather.precipitation_interval_end)
        assert(
          Date.parse(cp.weather.precipitation_interval_start) <
            Date.parse(cp.eta) &&
            Date.parse(cp.eta) <=
              Date.parse(cp.weather.precipitation_interval_end),
        );
      if (cp.risk === null) assert(cp.missing_fields.length > 0);
    }
  }
  report.routes = plan.routes.map((route, index) => ({
    distance_m: route.distance_m,
    duration_s: route.duration_s,
    checkpoints: route.checkpoints.length,
    coverage: route.coverage_fraction,
    geometry_sha256: shapes[index],
    notices: route.provider_notices.length,
  }));
  check(
    'real distinct truck routes, official totals, checkpoint chainage and ETA-aligned forecast intervals',
  );
  await expect(page.locator('.route-option')).toHaveCount(plan.routes.length);
  const reason = await page.locator('.recommendation-note').innerText();
  assert(plan.recommendation.reasons.length && reason.length > 15);
  if (plan.routes.length > 1) {
    await page.locator('.route-option').nth(1).click();
    await expect(page.locator('.route-option').nth(1)).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    await expect(page.locator('.map-shell')).toHaveAttribute(
      'data-selected-route',
      plan.routes[1].id,
    );
  }
  await page.locator('.checkpoint-list button').last().click();
  await expect(
    page.getByRole('complementary', { name: 'Checkpoint weather' }),
  ).toContainText('ETA');
  await expect(
    page.getByRole('complementary', { name: 'Checkpoint weather' }),
  ).toContainText('Wind valid');
  check('route selection, checkpoint inspector and recommendation explanation');
  const rawCorridor = await corridorResponse;
  assert(
    rawCorridor.ok(),
    `Live corridor failed: HTTP ${rawCorridor.status()}.`,
  );
  const corridor = await rawCorridor.json();
  assert.equal(corridor.frames.length, 49);
  assert(corridor.cells.length > 0 && corridor.cells.length <= 96);
  assert(
    corridor.frames.some((frame) =>
      frame.wind_mph.some((value) => value !== null),
    ),
    'No usable live corridor weather was returned.',
  );
  assert.equal(
    Date.parse(corridor.frames[48].valid_at) -
      Date.parse(corridor.frames[0].valid_at),
    48 * 3600000,
  );
  for (const frame of corridor.frames)
    assert.equal(frame.risk.length, corridor.cells.length);
  report.forecast = {
    cells: corridor.cells.length,
    frames: corridor.frames.length,
    missing_frames: corridor.frames_with_missing_data,
    frame0: corridor.frames[0].valid_at,
    frame48: corridor.frames[48].valid_at,
    measurements_changed:
      JSON.stringify(corridor.frames[0].wind_mph) !==
      JSON.stringify(corridor.frames[48].wind_mph),
  };
  const slider = page.getByRole('slider', { name: 'Forecast hour' });
  await slider.focus();
  await slider.press('End');
  await expect(slider).toHaveValue('48');
  await expect(page.locator('.forecast-map-label')).toContainText('+48h');
  await expect(page.locator('.forecast-time')).toContainText('+48');
  await slider.press('Home');
  await expect(slider).toHaveValue('0');
  assert.equal(await page.locator('.recommendation-note').innerText(), reason);
  assert.equal(report.requests.plans, 1);
  assert.equal(report.requests.corridor, 1);
  check(
    '49 frames, 0/48 endpoints, forecast labels, fixed recommendation and no extra planning requests',
  );
  await expect(page.locator('.map-shell')).toHaveAttribute(
    'data-map-ready',
    'true',
  );
  await page.locator('.map-shell').scrollIntoViewIfNeeded();
  await expect(page.locator('.maplibregl-canvas')).toBeVisible();
  await page.getByRole('button', { name: 'Zoom in' }).click();
  await page.getByRole('button', { name: 'Fit routes' }).click();
  const canvas = page.locator('.maplibregl-canvas');
  assert((await canvas.boundingBox()).height > 300);
  await page.screenshot({ path: `${output}/desktop.png` });
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .locator('.journey-bar')
    .evaluate((element) => element.scrollIntoView({ block: 'start' }));
  await page.getByRole('button', { name: 'Fit routes' }).click();
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await page.screenshot({ path: `${output}/mobile.png` });
  await slider.focus();
  await slider.press('End');
  await expect(slider).toHaveValue('48');
  await page.locator('.forecast-controls').scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${output}/mobile-forecast.png` });
  check(
    'desktop/mobile map controls, list alternative, timeline and no mobile horizontal overflow',
  );
  const scripts = await page
    .locator('script[src]')
    .evaluateAll((elements) => elements.map((element) => element.src));
  for (const url of scripts) {
    const response = await page.request.get(url);
    assert(
      response.ok() && !credentialPattern.test(await response.text()),
      'Credential pattern found in public entry asset (value omitted).',
    );
  }
  check(
    'credential patterns in entry assets and outgoing browser requests; exact local-secret bundle scan is separate',
  );
  assert.equal(
    report.errors.length,
    0,
    'Runtime or credential diagnostics failed.',
  );
  assert.equal(
    report.console_errors.length,
    0,
    'Console errors observed; inspect locally.',
  );
  assert.equal(
    report.network_errors.length,
    0,
    'Network failures observed; inspect sanitized report.',
  );
  report.status = 'passed';
} catch (error) {
  report.status = 'failed';
  report.failure =
    error instanceof Error
      ? error.message.split('\n')[0]
      : 'Acceptance failed.';
  process.exitCode = 1;
} finally {
  await writeFile(
    `${output}/report.json`,
    JSON.stringify(report, null, 2) + '\n',
  );
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
}
