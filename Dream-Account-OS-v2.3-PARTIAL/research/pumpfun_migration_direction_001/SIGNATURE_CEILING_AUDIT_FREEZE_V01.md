# PMD-001 — SIGNATURE CEILING AUDIT FREEZE V0.1

Date: 2026-09-16
Status: **RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME / AUDIT FROZEN**
Branch: `pumpfun-migration-direction-v0.1`

## Purpose

Before fetching full raw blocks for all 1,012 frozen candidates, PMD-001 will run a cheaper outcome-blind mathematical viability audit of final-curve source availability.

The audit asks only whether each mint-specific Pump bonding-curve PDA has successfully retrievable signature metadata inside the already-frozen `[T0-300s,T0)` interval.

No transaction bodies, price values, returns, PnL, direction labels or feature/outcome correlations are opened.

## Population

Exactly the frozen 1,012-candidate source-rebuild manifest identified by SHA-256:

`56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`

No row may be replaced or omitted because of source quality.

## Frozen method

For every candidate:

1. derive the mint-specific Pump bonding-curve PDA;
2. call `getSignaturesForAddress` with finalized commitment;
3. paginate until the history crosses strictly below `T0-300s` or is demonstrably exhausted;
4. count signature metadata only for `T0-300s <= blockTime < T0`;
5. separately count successful signatures where the signature metadata `err` is null;
6. record null timestamps, pagination failures, duplicate-signature conflicts and provider errors fail-closed.

The audit stores no post-T0 data as predictive evidence.

## Source ceiling logic

The final Source Gate requires at least 1,000 eligible reconstructed mints.

Therefore:

- if fewer than **1,000** of the 1,012 frozen candidates have at least one successful pre-T0 in-window signature under complete signature-history reconstruction, the full Source Gate is mathematically impossible under this mechanism and V0.1 fails closed before expensive block collection;
- if at least **1,000** candidates have at least one successful in-window signature and signature-history integrity is established, full block reconstruction remains authorized but the final Source Gate is **not yet passed**.

This audit does not lower or redefine the existing `n>=1000` gate.

## Provider/rate discipline

Public Solana RPC may be used for this bounded metadata audit only with conservative sequential pacing and retry/backoff. It must not be parallel-sharded in a way that intentionally overwhelms public infrastructure.

A paid/authenticated archival provider may be substituted only if its identity is recorded and its semantics remain standard Solana JSON-RPC. Provider changes are source-integrity events subject to reconciliation.

## Classification

- `SIGNATURE_CEILING_VIABLE`: complete source metadata exists for >=1,000 candidates with >=1 successful in-window signature.
- `SIGNATURE_CEILING_INSUFFICIENT`: complete source metadata proves <1,000 candidates with >=1 successful in-window signature.
- `SIGNATURE_CEILING_UNRESOLVED`: source/provider errors prevent a complete population-level conclusion.

None of these is an economic verdict.

Outcomes remain locked.
