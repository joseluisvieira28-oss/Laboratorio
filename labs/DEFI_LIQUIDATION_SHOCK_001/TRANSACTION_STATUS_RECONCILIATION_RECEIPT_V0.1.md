# DEFI-LIQUIDATION-SHOCK-001 — TRANSACTION STATUS RECONCILIATION RECEIPT V0.1

Date: 2026-09-17
Branch: `defi-liquidation-shock-v0.1`
Classification: `TRANSACTION_STATUS_SEMANTICS_PASS / ERR_IS_NULL_REJECTED / SOURCE_GATE_ACTIVE`

## Input

BigQuery result exported by the frozen query `source/BIGQUERY_TRANSACTION_STATUS_RECONCILIATION_V0_1.sql`.

Canonical local filename for the evidence: `DLS_TRANSACTION_STATUS_RECONCILIATION_V01.csv`
Uploaded/export filename: `bq-results-20260917-191002-1789672213621.csv`
SHA-256: `71502324c415bc511dfad8957d808ecc8a6eaa6c6884a412c31c9d6b583e0336`
Rows: 23
Unique signatures: 23
Exact duplicate rows: 0

Estimated BigQuery bytes before execution: 370.89 MB, below the 100 GB operational safety cap.

## Observed execution-state semantics

BigQuery `Transactions.status` separates the frozen sample as:

- `Success`: 14
- `Fail`: 9

Observed `err` semantics:

- all 14 `Success` rows have `err = ''` (empty string);
- all 9 `Fail` rows have a non-empty error string;
- `(err IS NULL)` is `FALSE` for all 23 rows.

Therefore the V0.1 helper expression `(err IS NULL) AS inferred_success_from_err` is NOT a valid success predicate for this public table and MUST NOT be used for the historical realized-liquidation census.

The canonical transaction-success predicate is frozen as:

```sql
status = 'Success'
```

For fail-closed consistency checking, a historical census may additionally require:

```sql
status = 'Success' AND COALESCE(err, '') = ''
```

Any row with inconsistent `status` / `err` semantics must be retained separately and treated as a source anomaly, not silently coerced into realized flow.

## Reconciliation against the frozen Helius RAW sample

The same 23 frozen signatures are present.

The BigQuery status distribution by candidate family is:

- Drift v2 / `liquidate_borrow_for_perp_pnl`: 0 success, 1 failed.
- Drift v2 / `liquidate_perp`: 2 success, 4 failed.
- Drift v2 / `liquidate_perp_pnl_for_deposit`: 1 success, 2 failed.
- Drift v2 / `liquidate_spot`: 6 success, 0 failed.
- marginfi v2 / `lending_account_liquidate`: 3 success, 0 failed.
- Save/Solend / `LiquidateObligationAndRedeemReserveCollateral`: 2 success, 2 failed.

This exactly matches the retained Helius RAW reconciliation receipt.

BigQuery failure error-code distribution is also identical to the retained RAW receipt:

- 5 × `0x1774` = decimal 6004 (Drift)
- 2 × `0x177a` = decimal 6010 (Drift)
- 2 × `0x1d` = decimal 29 (Save/Solend)

The retained repository RAW receipt records aggregate/family/error-class reconciliation but does not itself enumerate the signature→RAW-status map. The archival ZIP `DLS_RAW_SAMPLE_VERIFY_20260916_221907.zip` remains the byte-level authority for the already completed 23/23 RAW reconciliation.

## Frozen scientific rule

A discriminator match alone is a liquidation candidate, not realized forced flow.

A realized liquidation candidate must satisfy all of the following before any economic test:

1. frozen discriminator/tag match;
2. historically valid decoder authority for the protocol/date interval;
3. transaction execution state `status = 'Success'`;
4. any required RAW archival validation / class validation under the existing source governance.

Failed transactions remain retained as `LIQUIDATION_ATTEMPT_FAILED` source evidence and MUST NOT be counted as realized forced-flow events.

## Current scientific state

This closes the BigQuery transaction-status semantics gate.

It does NOT grant `SOURCE_DATA_PASS`.
Historical decoder authority remains partial and the bounded historical candidate census has not yet been executed.

No prices, returns, PnL, market direction, protected outcomes, live trading, exchange mutation, wallet action, alert/webhook, or main merge occurred.
