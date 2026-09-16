# DEFI-LIQUIDATION-SHOCK-001 — RAW VALIDATION SAMPLE AUDIT V0.1

Date: 2026-09-16
Branch: `defi-liquidation-shock-v0.1`
Classification: `SAMPLE_STRUCTURE_PASS / RAW_RPC_VALIDATION_PENDING`

## Input

File: `DLS_RAW_VALIDATION_SAMPLE_V01.csv`
SHA-256: `b58af58b0229969d38625cc2c4e138742477b1633d3fc06f3fa6b328064d5bdc`
Rows: 23
Unique transaction signatures: 23
Exact duplicate rows: 0
Duplicate scientific identity keys: 0

## Structural checks

The sample contains the required verifier fields and is deterministic by `sample_rank` within protocol / match / instruction-location groups.

All 23 `data` Base58 payloads were independently decoded locally and the decoded byte prefixes matched the frozen `reference_prefix_hex` for all 23 rows.

Outer/inner consistency:
- outer rows have null `parent_index`;
- inner rows have non-null `parent_index`.

## Sample composition

- Drift v2 / `liquidate_borrow_for_perp_pnl`: 1 outer
- Drift v2 / `liquidate_perp`: 3 outer + 3 inner
- Drift v2 / `liquidate_perp_pnl_for_deposit`: 3 outer
- Drift v2 / `liquidate_spot`: 3 outer + 3 inner
- marginfi v2 / `lending_account_liquidate`: 3 outer
- Save/Solend / `LiquidateObligationAndRedeemReserveCollateral`: 1 outer + 3 inner

No Kamino candidate and no Save/Solend `LiquidateObligation` (`0x0c`) candidate occurred in the sampled smoke-test day, so this sample does not validate those absent candidate classes.

## Scientific interpretation

This is NOT historical decoder authority and NOT SOURCE_DATA_PASS.
It proves only that the BigQuery sample is internally consistent and suitable for raw archival RPC reconciliation.

Next required gate: reconcile all 23 unique signatures through archival `getTransaction` and verify slot, blockTime, program ID, outer/CPI location and discriminator bytes. Historical decoder authority remains a separate requirement.

No prices, returns, PnL, direction, protected outcomes, live trading, exchange mutation or main merge were involved.
