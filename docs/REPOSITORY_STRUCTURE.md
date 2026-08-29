# Repository Structure

This repository is organized as a two-application monorepo with a deterministic legacy materialization layer.

```text
/
├─ web/
│  ├─ src/
│  │  ├─ app/
│  │  ├─ modules/
│  │  └─ shared/
│  ├─ public/
│  │  └─ assets/
│  └─ tests/
├─ api/
│  ├─ src/
│  │  ├─ modules/
│  │  ├─ shared/
│  │  └─ config/
│  ├─ contracts/
│  └─ tests/
├─ scripts/
├─ docs/
├─ mockups/
├─ .bootstrap/
└─ .github/
```

## Ownership

- `web/` is the only canonical frontend application boundary.
- `web/src/` is the only committed frontend source tree. A root-level `src/` is forbidden.
- `web/public/assets/` owns committed public brand assets.
- `web/tests/` is the canonical frontend-test boundary. Existing legacy test runners under `scripts/` remain temporary tooling until they are migrated without losing certification coverage.
- `api/` is the canonical backend application boundary. The backend is not implemented yet; this directory defines structure and contracts only and must not contain fake persistence, fake authentication, fake endpoints or simulated integrations.
- `api/contracts/` owns future request/response schemas and cross-boundary contracts.
- `scripts/` is repository tooling: materialization, migration, certification and temporary compatibility orchestration. Product source does not belong there permanently.
- `.bootstrap/` is a legacy deterministic source payload used only by `scripts/materialize.py` while the application is migrated away from the historical generated bundle.
- `mockups/` remains isolated fixture support for explicit mock mode and never represents production records.

## Runtime compatibility

Some historical materializers still resolve files from root-level `src/` and root-level `assets/`. Those paths are no longer committed owners. `scripts/materialize.py` creates a temporary compatibility copy from `web/src/` and stages `web/public/assets/` only while materialization is executing, then removes the temporary `src/` tree.

This compatibility layer is transitional tooling, not repository architecture.

## Structural rules

1. Development is performed on `dev` unless explicitly authorized otherwise.
2. `main` remains untouched.
3. There is one canonical owner for each domain and public asset.
4. `dashboard` and `agenda` are global modules and cannot live under CRM.
5. Backend functionality is not simulated before a real implementation exists.
6. Clean checkout must not contain generated `app.js`, `index.html`, root `assets/`, root `src/` or `_site/`.
7. CI materializes from a clean checkout and validates generated output separately from committed source.
8. GitHub Pages publishes only the certified materialized artifact.
9. Temporary compatibility and one-shot migration code must be removed once no consumer depends on it.

## Frontend module structure

Canonical modules live under `web/src/modules/`:

- `dashboard`
- `agenda`
- `crm`
- `finance`
- `legal`
- `business`
- `marketing`
- `communications`
- `integrations`
- `settings`
- `notifications`

Domain internals remain owned by their module. For example, Finance owns Transactions, Accounting, Fiscal Documents, Allocations, Participations and Payouts; Legal owns Contracts, Matters, Compliance, Intellectual Property and Corporate Governance.

## Backend preparation

`api/src/` contains only architectural boundaries until backend implementation begins:

- `modules/` — future backend domain modules.
- `shared/` — future shared backend primitives.
- `config/` — future validated runtime configuration.
- `contracts/` — stable frontend/backend contracts independent of runtime implementation.
- `tests/` — future API unit/integration tests.

No backend file should claim a provider, database, authentication state, external API connection or successful integration until it exists and is validated.
