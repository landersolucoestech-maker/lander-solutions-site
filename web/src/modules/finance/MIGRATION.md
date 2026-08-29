# Finance source ownership

Canonical finance source files live under this module. Legacy materializer entry points remain in `scripts/` during the deterministic migration, but they must read domain/browser/style sources from `src/modules/finance/*`.

Subdomains: transactions, accounting, fiscal, allocations, participations and payouts.
