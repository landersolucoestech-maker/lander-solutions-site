# Web Architecture

`web/` is the only canonical frontend application boundary.

- `src/app/` — application shell, routing and bootstrap boundaries.
- `src/modules/` — functional product modules.
- `src/shared/` — shared frontend primitives.
- `public/assets/` — committed public assets.
- `tests/` — canonical frontend test boundary.

Global modules such as Dashboard and Agenda remain top-level modules. CRM owns only relationship/commercial concerns. Product source must not be reintroduced under root-level `src/` or under `scripts/`.

The deterministic materializer still exists as transitional tooling. It may create temporary compatibility paths at runtime, but committed frontend ownership remains exclusively under `web/`.
