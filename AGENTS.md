# Project standards

Build Weather-Aware Truck Routing with React and Django. The authoritative specification is [docs/fs-assessment-spotter.pdf](docs/fs-assessment-spotter.pdf); it wins over preferences and planning assumptions. Read docs/ASSESSMENT.md, ARCHITECTURE.md, DECISIONS.md, and PLAN.md before implementation.

- Current phase: implementation explicitly authorized on November 1, 2026. Implement Milestone 1 (foundation, provider proof, pure domain logic and verification). Do not push or deploy without further authorization.
- Keep code small, explicit, understandable, and maintainable. Add abstractions only when a concrete need exists.
- Keep HERE/Open-Meteo adapters separate from deterministic sampling, risk, aggregation, and ranking logic. No network calls in domain functions.
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
