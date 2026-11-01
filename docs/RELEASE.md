# GitHub release and hosting handoff

GitHub publication was explicitly authorized. Cloud-resource creation, deployment, paid services and payment methods remain unauthorized. No hosted app URL or recorded Loom exists yet.

## Published history and verification

The existing public repository was empty (`isEmpty=true`, no remote heads). The reviewed application was published by normal push at `28e8e23cd77b0b7ca65332b35c9c0d56c7299b69`; no remote work was overwritten. All subsequent pushes must fetch and check ancestry again.

The first real [GitHub run](https://github.com/UsmanPrime/Weather-Aware-Truck-Routing/actions/runs/41300829582) passed backend CI but failed frontend clean installation: npm 11.19.1 rejected missing bundled optional `@emnapi/core` and `@emnapi/runtime` metadata. Local npm 11.6.1 had accepted that lock. Commit `3b0bd5a41bdf4764b680a435aca05826413e6d05` adds those bundled entries using the runner's supported resolver, without changing any existing package version. A real local `npm ci`, 25 unit tests and production build then passed. The [follow-up run](https://github.com/UsmanPrime/Weather-Aware-Truck-Routing/actions/runs/41301202496) completed successfully with both backend and frontend jobs passing. Its receipt is evidence/github-ci.json. Consult live Actions for the later handoff commit rather than assuming its result from configuration.

Release preflight reran 225 backend tests, 25 frontend unit tests and 20 desktop/mobile Playwright cases: zero failures. Ruff, formatting, ESLint, TypeScript, Django checks and production build passed. An extended secret scan includes tracked source, every reachable history blob, exact configured local secret values and all seven generated frontend asset files; no findings. The local .env remains ignored. These are focused checks, not a guarantee for every secret format.

## Deployment proof and remaining limits

The actual frozen production environment was installed in the existing WSL Linux runtime with Python 3.13.17 and Gunicorn 26.2.0. [Linux receipt](evidence/linux-production.json): five checks passed using the real one-process/four-thread server: health/security headers, HTTPS redirect, accepted CORS origin, rejected origin and JSON POST preflight. An initial 20-second probe timed out during cold imports on the Windows-mounted filesystem; a 45-second bounded startup probe and its repeat passed. The verifier is now in Linux CI. This proves loopback behavior with a simulated trusted proxy, not Render's actual public TLS.

The public acceptance script was rehearsed against the built production frontend with real providers: three distinct Fort Worth-Dallas truck routes, full ETA forecast coverage, 35 cells, 49 frames, one plan and one corridor request, no page/console/network errors and usable desktop/mobile controls. The timestamped receipt in `evidence/public-rehearsal.json` records local first-health timing and explicitly skips public TLS/CORS; it is not a hosted cold-start measurement. Future public results must use actual deployed origins.

`render.yaml` contains one explicitly Free Python service and one static site, with no paid compute plan, database or other resource. Auto-deploy/previews are off. Static sites do not use a compute plan; adding a `plan` field to that resource is not needed to select free static hosting. The blueprint was validated against Render's public JSON Schema. Manual settings, secure secret entry, exact host/CORS handling, SPA rewrite and build/start commands are in [DEPLOYMENT.md](DEPLOYMENT.md).

Known non-blocking local findings remain visible: lazy MapLibre bundle-size warning, twelve moderate development-tool audit entries, two deliberate HSTS scope/preload warnings and software-renderer samples that do not establish a 50 ms target. ORS truck ETAs exclude live traffic/driver breaks; free alternatives and forecast coverage are provider dependent. Open-Meteo free use remains noncommercial. No deployment, cost, safety or interview outcome is guaranteed.

## After hosting approval

1. Create only the two documented free services from the published `main`, without a payment method. Stop if the account requires paid resources or card details.
2. Keep backend keys only in Render's environment, generate a stable Django secret, disable debug and configure exact actual frontend origin. Rebuild the frontend with the actual backend API URL.
3. Run [PUBLIC_ACCEPTANCE.md](PUBLIC_ACCEPTANCE.md) once against the actual HTTPS origins, review screenshots/console and manually inspect map/corridor details. Preserve truthful cold-start/failure receipts.
4. Add verified demo URLs to README. Record the [7-9-minute speaking outline](WALKTHROUGH.md), verify its access/duration and add the real Loom link.
