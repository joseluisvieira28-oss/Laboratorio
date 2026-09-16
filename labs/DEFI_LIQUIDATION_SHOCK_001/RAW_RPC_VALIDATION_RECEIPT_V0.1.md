# DEFI-LIQUIDATION-SHOCK-001 — RAW RPC VALIDATION RECEIPT V0.1

Date: 2026-09-16
Branch: `defi-liquidation-shock-v0.1`
Classification: `RAW_RPC_RECONCILIATION_PASS / SUCCESS_FILTER_REQUIRED / HISTORICAL_DECODER_AUTHORITY_PENDING`

## Input evidence

ZIP: `DLS_RAW_SAMPLE_VERIFY_20260916_221907.zip`
ZIP SHA-256: `5e14c1712a97d60983b7321735615681671b76dcb1bce5f973dfdb28f3cfab7f`
CSV input SHA-256: `b58af58b0229969d38625cc2c4e138742477b1633d3fc06f3fa6b328064d5bdc`
Verifier: `DLS_BIGQUERY_RAW_VERIFY_V01`
Run status: `RAW_VERIFICATION_COMPLETE`
RPC requests: 23
Unique candidate transactions attempted: 23 / 23
Partial due to safety cap: false

## Independent re-audit

The uploaded ZIP was independently re-opened and checked after the runner completed.

- 27 ZIP members total: 23 exact raw `getTransaction` JSON responses plus `CANDIDATE_SUMMARY.json`, `RPC_RECEIPTS.json`, `RUN_MANIFEST.json`, and `VERIFICATION_ROWS.jsonl`.
- Receipt request IDs are exactly sequential 1..23.
- All 23 raw-response byte lengths match the receipt ledger.
- All 23 raw-response SHA-256 values match the receipt ledger.
- All 23 transaction signatures are unique and reconcile to the 23 frozen CSV rows.
- All 23 raw transaction slots match BigQuery `block_slot`.
- All 23 raw `blockTime` values match BigQuery `block_timestamp` at Unix-second resolution.
- All 23 protocol program IDs match at the frozen outer/CPI instruction location.
- All 23 raw Base58 instruction payloads decode to bytes whose prefix matches the frozen `reference_prefix_hex`.
- All 23 full `data` strings match the BigQuery instruction payloads exactly.
- No structural mismatch was found.

Result: `23/23 RAW_RECONCILED`.

## Transaction success state

The raw RPC sample contains 14 successful transactions and 9 failed transactions.

By candidate family:

- Drift v2 / `liquidate_borrow_for_perp_pnl`: 0 success, 1 failed.
- Drift v2 / `liquidate_perp`: 2 success, 4 failed.
- Drift v2 / `liquidate_perp_pnl_for_deposit`: 1 success, 2 failed.
- Drift v2 / `liquidate_spot`: 6 success, 0 failed.
- marginfi v2 / `lending_account_liquidate`: 3 success, 0 failed.
- Save/Solend / `LiquidateObligationAndRedeemReserveCollateral`: 2 success, 2 failed.

The failed transactions are retained as source evidence of liquidation attempts but MUST NOT be counted as realized forced-flow liquidation events. Solana transactions are atomic: a failed transaction does not commit the instruction state changes. The event census therefore requires an explicit successful-transaction filter before any sample gate or economic test.

Observed failed-transaction RPC errors in this sample:

- 5 Drift transactions: custom error 6004.
- 2 Drift transactions: custom error 6010.
- 2 Save/Solend transactions: custom error 29.

No attempt is made here to interpret those custom error codes economically.

## Coverage limitation

This sample validates the classes present on 2024-12-15 only.

It does NOT validate:
- Kamino Lend, because no Kamino liquidation-reference candidate occurred in the smoke-test day;
- Save/Solend native tag `0x0c` (`LiquidateObligation`), because no `0x0c` candidate occurred in the smoke-test day;
- historical decoder authority outside the already documented source intervals.

## Scientific consequence

The BigQuery → Helius raw-reconciliation route is technically validated on the sampled candidate classes, including outer and inner/CPI locations.

This is NOT `SOURCE_DATA_PASS` yet.

Before a full historical candidate census is accepted, the lab must:

1. apply or reconcile transaction success state so failed attempts do not contaminate the realized forced-flow population;
2. complete protocol/interval historical decoder authority;
3. validate candidate classes absent from the current sample when they first occur;
4. run the bounded historical census under the existing source-only / outcome-blind firewall;
5. audit completeness and freeze the numerical sample gate before Discovery.

No prices, returns, PnL, market direction, protected outcomes, live trading, exchange mutation, wallet action, or main merge occurred.
