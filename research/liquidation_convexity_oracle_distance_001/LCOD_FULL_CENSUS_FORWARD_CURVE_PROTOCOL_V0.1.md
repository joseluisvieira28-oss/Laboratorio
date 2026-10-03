# LCOD FULL-CENSUS FORWARD CURVE PROTOCOL V0.1

Frozen: 2026-09-24
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Stage: M2 SOURCE / FORWARD MECHANISM
Outcomes: CLOSED

## Preconditions already satisfied

- Aave v4 borrower index census: CENSUS_INDEX_SOURCE_PASS.
- 92/92 reserves visited.
- 3,149 raw borrower rows.
- 2,386 deduplicated borrowers.
- zero census query errors.
- raw-component HF reconciliation: FORWARD_COMPONENT_SOURCE_RECONCILIATION_PASS.
- frozen acceptable relative HF reconstruction error <= 5e-5.

## Canonical forward population

At one UTC snapshot boundary, enumerate the complete borrower index obtainable
from all 92 v4 reserves using the frozen pagination route.

Deduplicate by wallet identity in-memory. Raw wallet addresses MUST NOT be
retained in the durable scientific receipt; use SHA-256 identifiers.

Every borrower then receives component reads for every v4 spoke returned by
get_user_positions.

A borrower is CANONICAL_CURVE_ELIGIBLE only if:
1. every supply/borrow component required for its health calculation is present;
2. collateral flag and reserve identity are resolved;
3. reserve priceUsd and collateralFactorPct are present;
4. debt balance reconciles to principal + interest;
5. reconstructed HF agrees with official Aave health semantics within <= 5e-5.

Missing/inconsistent borrowers are excluded with a frozen reason code, never
imputed.

## Frozen coverage gate

The full-census forward snapshot is scientifically usable only if:
- >= 90% of debt-bearing indexed borrowers are CANONICAL_CURVE_ELIGIBLE;
- zero unresolved duplicate borrower identities;
- zero reserve pagination errors;
- zero silent component-read errors;
- exact captured_at_utc is preserved.

If the gate fails: SOURCE_SNAPSHOT_INCOMPLETE. Do not lower it.

## Frozen shock operator

For V0.1 only, apply the same proportional shock to every collateral USD value
within each eligible borrower while debt is held static.

Frozen grid:
0%, -0.25%, -0.50%, -0.75%, -1.00%, -1.50%, -2.00%, -3.00%, -5.00%.

At each shock report:
- newly HF<1 borrower count;
- newly eligible debt USD;
- cumulative eligible debt USD;
- first difference across adjacent frozen shock points;
- second difference across adjacent frozen shock points.

This uniform-collateral operator is a mechanism diagnostic, not a market model.

## Promotion firewall

This protocol may establish a reproducible forward liquidation-convexity state.
It earns NO trading-edge promotion by itself.

Forbidden at this stage:
- BTC/ETH/alt returns;
- liquidation-event outcomes;
- CEX/DEX response;
- direction;
- PnL;
- threshold selection from the curve;
- choosing a preferred shock point after inspection.

Any market-response experiment requires a separate pre-outcome freeze.
