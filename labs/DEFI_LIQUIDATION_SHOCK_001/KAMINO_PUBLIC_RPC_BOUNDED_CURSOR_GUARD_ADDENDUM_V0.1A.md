# DEFI-LIQUIDATION-SHOCK-001 — KAMINO BOUNDED RPC CURSOR GUARD ADDENDUM V0.1A

Date: 2026-09-22  
Status: **FROZEN PRE-PHASE-A EXECUTION / TECHNICAL BOUNDARY-COMPLETENESS CORRECTION**

This addendum refines only cursor placement in the already-frozen public-RPC transport. No candidate or liquidation transaction body has been opened under the bounded first-success execution.

## Problem prevented

An arbitrary `until` signature selected from the exact start-boundary block could theoretically sit between other transactions in that same slot. Using it as the terminal cursor might omit Kamino-address transactions in the same start slot.

## Frozen guard rule

For every chunk:

- **start guard cursor**: one ordinary finalized transaction signature from the nearest valid block whose `blockTime < chunk_start_utc`;
- **end cursor**: one ordinary finalized transaction signature from a valid block whose `blockTime >= chunk_end_utc_exclusive`.

Enumerate program-address signatures between those guards, then define the scientific chunk solely by timestamp:

`chunk_start_utc <= blockTime < chunk_end_utc_exclusive`.

Rows returned only because of guard width are retained in transport evidence but excluded from the chunk by the pre-frozen timestamp rule.

This guarantees the transport cursor cannot cut away same-block transactions at the inclusive start boundary.

All other V0.1 rules remain unchanged.
