# ETH-STAKING-FLOW-001 — V3 STAGE-A CLICKHOUSE PARQUET READER V0.1.8

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND
Parent: V0.1.7 alternate-reader remediation

## Purpose

Attempt exact recovery of the same seven immutable Xatu canonical_beacon_validators Parquet objects with ClickHouse-local, an independent Parquet implementation explicitly documented by Xatu for public Parquet querying.

No source semantics change.

## Exact source and objects

Base:
https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators

Object:
YYYY/M/D/0.parquet

Only the same three controls and seven frozen missing dates may be opened.

No adjacent date, no alternate hour, no alternate table, no current state.

## Reader

Docker image:
clickhouse/clickhouse-server:25.8

The workflow must record the resolved Docker image ID/digest when available.

Reader command:
clickhouse local + url(..., 'Parquet').

## Exact reconstruction

For each date D:
- T = minimum actual epoch_start_date_time in the exact Parquet object;
- require midnight(D) <= T <= midnight(D)+384 seconds;
- select only rows at T;
- require row count > 0;
- require zero null validator indices;
- require uniqExact(index) == row count;
- require uniqExact(epoch) == 1;
- count pending_queued;
- count active_exiting;
- net_queue = pending_queued - active_exiting.

## Controls

Must match exactly:
- 2025-02-24: epoch 347738, unix 1740355415, pending 0, exiting 5, net -5
- 2025-03-02: epoch 349088, unix 1740873815, pending 0, exiting 0, net 0
- 2025-10-17: epoch 400613, unix 1760659415, pending 48, exiting 55209, net -55161

Any mismatch => SOURCE_PROVENANCE_FAILURE.

## Missing dates

Only after 3/3 control PASS:
- 2025-02-25 epoch 347963
- 2025-02-26 epoch 348188
- 2025-02-27 epoch 348413
- 2025-02-28 epoch 348638
- 2025-03-01 epoch 348863
- 2025-10-18 epoch 400838
- 2025-10-19 epoch 401063

CLICKHOUSE_PARQUET_RECOVERY_PASS requires 7/7 exact date/epoch/integrity PASS.

## Reader cross-check

If a durable V0.1.7 DuckDB recovery receipt exists on the branch, every recovered pending/exiting/net count MUST agree exactly between V0.1.7 and V0.1.8.

Disagreement => SOURCE_PROVENANCE_FAILURE.

DuckDB failure/absence does not itself invalidate a ClickHouse recovery because both are parser implementations over the same immutable source bytes.

## Firewall

SOURCE ONLY.
No signal evaluation.
No ETH/BTC market data.
No returns/PnL.
No source after 2026-08-31.
No live trading or mutation.
No main merge.
