# LCOD COMPONENT SNAPSHOT CONTRACT V0.1

Frozen: 2026-09-24
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Stage: SOURCE / MECHANISM ONLY

## Canonical position snapshot

Each accepted V4 position must be representable as:

- snapshot_id
- captured_at_utc
- chain_id
- spoke_id
- position_id_hash
- official_health_factor
- supply legs[]
  - reserve_id
  - amount_main_units
  - oracle_price_usd
  - collateral_factor_pct
  - collateral_enabled
- borrow legs[]
  - reserve_id
  - principal_main_units
  - accrued_interest_main_units
  - oracle_price_usd
- reserve metadata provenance
- source response hashes

Wallet addresses are not persisted in the canonical research row after in-run joins; use a one-way hash if an identity key is necessary for deduplication.

## V4 reconstructed health

For source reconciliation only:

collateral_capacity_usd =
SUM(collateral_enabled * supply_amount * oracle_price_usd * collateral_factor_pct / 100)

debt_usd =
SUM((principal + accrued_interest) * oracle_price_usd)

reconstructed_health_factor =
collateral_capacity_usd / debt_usd

Debt <= 0 positions are excluded from the liquidation-convexity population.

## Important source constraint

The live Aave tool description says V4 collateralFactorPct is the liquidation boundary because V4 has no separate liquidationThreshold field.

Do not substitute:
- LTV;
- borrow cap;
- supply cap;
- risk-premium weight;
- current aggregate HF as an input.

Official HF is a reconciliation target only.

## Reconciliation gate before real curve construction

No real borrower enters an LCOD curve until:
1. component fields are sourced without imputation;
2. official health factor is available;
3. reconstructed HF is computed from component fields;
4. reconciliation error distribution is recorded on an outcome-blind source sample;
5. a numerical tolerance is frozen from representation/rounding evidence;
6. the frozen tolerance is then applied prospectively.

The tolerance is deliberately NOT specified in this document because component precision has not yet been observed. It may not be chosen from liquidation or market outcomes.

## Minimum source calibration

Before SOURCE_DATA_PASS:
- >= 25 debt-bearing V4 positions with complete component data;
- >= 90% of sampled debt-bearing positions must be reconstructable without missing required fields;
- zero use of market returns, liquidation outcomes or PnL;
- all exclusions must carry a deterministic source reason.

Passing source calibration does not imply predictive edge.
