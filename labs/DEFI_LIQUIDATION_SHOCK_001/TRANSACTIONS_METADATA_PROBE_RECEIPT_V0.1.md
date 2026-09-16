# DEFI-LIQUIDATION-SHOCK-001 — TRANSACTIONS METADATA PROBE RECEIPT V0.1

Date: 2026-09-16
Branch: `defi-liquidation-shock-v0.1`
Status: `METADATA_PASS / OUTCOME-BLIND`

## Observed BigQuery schema metadata

Table: `bigquery-public-data.crypto_solana_mainnet_us.Transactions`

Confirmed from the metadata probe:

- `block_timestamp` — `TIMESTAMP` — partitioning column = YES
- `signature` — `STRING` — clustering ordinal position = 1
- `status` — `STRING`
- `err` — `STRING`

Other displayed columns included `block_slot`, `block_hash`, `recent_block_hash`, `index`, `fee`, `compute_units_consumed`, `accounts`, `log_messages`, `balance_changes`, `pre_token_balances`, and `post_token_balances`.

## Scientific consequence

The historical source path can use:

1. `block_timestamp` for partition pruning;
2. exact transaction `signature` for cluster pruning;
3. `status` / `err` for transaction execution-state reconciliation.

Before any historical census is allowed to treat `err IS NULL` (or any `status` value) as an authoritative success filter, the semantics must be reconciled against the already frozen 23-signature Helius RAW validation sample.

No prices, returns, PnL, direction, protected outcomes, live trading, exchange mutation or main merge are involved.
