# Project standards

Build Weather-Aware Truck Routing with React and Django. The authoritative specification is [docs/fs-assessment-spotter.pdf](docs/fs-assessment-spotter.pdf); it wins over preferences and planning assumptions. Read docs/ASSESSMENT.md, ARCHITECTURE.md, DECISIONS.md, and PLAN.md before implementation.

- Current phase: full assessment implementation authorized, November 1–4, 2026. Complete and verify successive local milestones. Default providers: free OpenRouteService driving-hgv, HeiGIT Pelias and Open-Meteo. Do not push, publish, deploy or create paid resources without further authorization.
- Keep code small, explicit, understandable, and maintainable. Add abstractions only when a concrete need exists.
- Keep ORS/Pelias/Open-Meteo adapters separate from deterministic sampling, risk, aggregation, and ranking logic. Retain optional HERE support without requiring its credentials. No network calls in domain functions.
- Use TypeScript contracts, Python typed structures, explicit units, timezone-aware instants, and structured errors. Validate external data at adapter boundaries.
- Never commit credentials, credential-bearing URLs, or .env files. Supply placeholder-only .env.example files during implementation. Keep provider keys on Django.
- Never fabricate successful API responses or test results. Fixtures must be visibly identified in tests, documentation, and any demo mode; never present them as live observations.
- Preserve forecast provenance, retrieval times, valid times, missingness, and coverage. Missing weather is unknown, never Low risk.
- Follow the exact PDF load rules even if counterintuitive. Record any interpretation of an ambiguity in DECISIONS.md and cover it with tests.
- Test threshold boundaries, units, distance/time conservation, unknown weather, and route ordering independently of providers. Use controlled fixtures for reproducible integration and browser tests; label real-provider smoke checks separately.
- Use semantic accessible UI, keyboard-operable map alternatives, honest loading/error states, visible units and timezones, and reduced-motion support.
- Run checks appropriate to changes; report what ran, what passed, and what remains unverified. Do not claim deployment or live-provider validation without evidence.
- Keep deployment configuration minimal. No database, task queue, accounts, or persistent trip history without a demonstrated requirement.
- Do not silently reduce requested checkpoint spacing, manufacture route alternatives, or substitute car routes for truck routes.

Keep the requirement matrix and decisions current as implementation changes. Review progress against docs/PLAN.md before expanding scope.

Submission checkpoint: the full local routing/map/corridor application and release configuration are implemented. FINAL_AUDIT.md records evidence and limitations. Remaining delivery work is approved publication, hosted verification and a real Loom recording; do not infer approval from prepared release instructions.
