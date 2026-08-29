# API

`api/` is the canonical backend application boundary for the project.

The backend is intentionally **not implemented yet**. This tree exists now so the repository does not require another structural migration when backend work starts.

- `src/modules/` — future backend domain modules.
- `src/shared/` — future shared backend primitives.
- `src/config/` — future validated runtime configuration.
- `contracts/` — frontend/backend request, response and event contracts.
- `tests/` — future backend tests.

Do not add fake endpoints, persistence, authentication, jobs, queues, secrets, provider connections or integration-success states before a real runtime exists.
