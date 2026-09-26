# SOURCE GATE V0.1

Frozen: 2026-09-24

## Official source facts

Aave documents health factor as:
(total collateral value * weighted average liquidation threshold) / total borrow value,
with HF < 1 defining liquidation eligibility.

Current Aave read surfaces expose markets/reserves, user positions and user summaries. Protocol/risk parameters can change through governance and must be versioned at the measurement boundary.

Primary references:
- https://aave.com/help/borrowing/liquidations
- https://aave.com/docs
- https://aave.com/docs/mcp/tools

## Required state for one canonical snapshot

For every borrower included:
- chain and market/deployment identity;
- borrower address/opaque position identity;
- collateral balances by reserve;
- debt balances by reserve;
- collateral-enabled state;
- eMode/isolation state where applicable;
- liquidation threshold applicable to each collateral;
- oracle price used for each collateral and debt asset;
- block number / block timestamp or equivalent immutable state boundary;
- data-source coverage metadata.

## Frozen shock grid

V0.1 source/mechanism grid:
0, -0.25%, -0.50%, -0.75%, -1.00%, -1.50%, -2.00%, -3.00%, -5.00%

The grid is applied only to an explicitly named collateral/oracle factor or to a separately frozen correlated basket. No after-the-fact asset-specific shock grid.

## Outputs before any market outcome

For each shock:
- borrowers newly crossing HF < 1;
- debt value newly liquidation-eligible;
- collateral value attached to newly eligible positions;
- cumulative eligible debt;
- first difference of eligible debt;
- second difference / convexity diagnostic.

## Source verdict

SOURCE_PARTIAL.

Why not PASS yet:
- AAVE-HF-CROWDING-001 proves a borrower population read route exists, but this new lab needs position-component completeness sufficient to reprice collateral/debt under shocks rather than merely read current HF.
- historical parameter/oracle reconstruction has not yet been proven for retrospective use.
- therefore V0.1 may begin with FORWARD snapshot construction; historical Discovery remains blocked until exact state reconstruction is proven.

## Fail-closed rules

1. Current HF is never reverse-engineered into historical HF.
2. Missing collateral/debt component => borrower excluded with explicit reason; never imputed.
3. Missing oracle price or liquidation threshold => position cannot contribute to canonical curve.
4. Current governance parameter must not be applied to an earlier block.
5. Different chains/markets are not pooled until state semantics are proven equivalent.
6. Existing AAVE-HF-CROWDING snapshots may be reused only as raw/source evidence where fields are sufficient; its frozen HF<1.10 threshold is not imported as this lab's predictor.
