# LCOD FULL-CENSUS SHARD-0 ENGINEERING PREFLIGHT FREEZE V0.1

Frozen: 2026-09-24
Parent: LCOD_FULL_CENSUS_FORWARD_CURVE_PROTOCOL_V0.1
Purpose: source-engineering feasibility only.

## Deterministic shard
Re-enumerate the complete Aave v4 borrower index through the exact census route.
Include a borrower in this preflight iff:
SHA256(lowercase wallet address).hexdigest()[0] == "0"

No borrower is selected by health factor, collateral, debt, value or outcome.

## What this preflight may measure
- number of indexed borrowers in shard 0;
- current debt-bearing borrowers;
- component-read completeness;
- official-vs-reconstructed HF relative error;
- source/read errors and exclusion reason counts.

## Frozen pass condition
Among shard-0 borrowers that currently expose at least one debt-bearing v4 position:
- >=90% must be component-complete and every debt-bearing position must reconcile
  to the official Aave health factor within the already frozen <=5e-5 tolerance;
- zero silent read errors;
- all exclusions must be explicit.

This preflight does NOT compute the liquidation shock curve and earns ZERO edge
or promotion credit. Passing only authorizes scaling the same source plumbing
to all 16 deterministic SHA-prefix shards.

No market return, liquidation outcome, PnL, direction, live trading or mutation.
