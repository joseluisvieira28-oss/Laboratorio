# ETH-STAKING-FLOW-001 — V3 STAGE-A ALTERNATE PARQUET READER V0.1.7

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND
Parent state: V3 Stage-A SOURCE_ACQUISITION_TECHNICAL_FAILURE

## Purpose

Recover the exact seven Stage-A dates from the SAME immutable Xatu public Parquet objects using an independent Parquet implementation.

This is not a new economic source.
It is a technical parser/reader remediation against the already-authorized canonical Xatu source.

## Exact immutable source

Base:
https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators

Object for UTC date D:
YYYY/M/D/0.parquet

No adjacent date.
No alternate hour.
No different table.
No alternate timestamp.
No current-state substitution.

## Reader implementation

Primary alternate engine:
DuckDB Python package version 1.4.1.

DuckDB must read the Parquet object directly and derive source state only from:
- epoch
- epoch_start_date_time
- index
- status.

No PyArrow result is used to derive a recovered value.

The engine/version is transport/parser metadata only.

## Exact timestamp semantics

For each date:
1. compute UTC midnight;
2. identify the minimum actual epoch_start_date_time exposed by the Parquet object;
3. require UTC midnight <= T <= midnight + 384 seconds;
4. select ONLY rows with epoch_start_date_time == T;
5. require >0 rows;
6. require index non-null and COUNT(DISTINCT index) == row count;
7. require exactly one distinct epoch;
8. count status == pending_queued;
9. count status == active_exiting;
10. net_queue = pending_queued - active_exiting.

This is byte/semantic equivalent to the original V0.3D object/time rule.

## Frozen control objects

DuckDB MUST reproduce exactly:

2025-02-24:
- epoch 347738
- unix 1740355415
- pending_queued 0
- active_exiting 5
- net_queue -5

2025-03-02:
- epoch 349088
- unix 1740873815
- pending_queued 0
- active_exiting 0
- net_queue 0

2025-10-17:
- epoch 400613
- unix 1760659415
- pending_queued 48
- active_exiting 55209
- net_queue -55161

Any control mismatch = SOURCE_PROVENANCE_FAILURE / STOP.

## Frozen missing objects

Only after 3/3 control PASS may the reader open:

- 2025-02-25 — expected epoch 347963
- 2025-02-26 — expected epoch 348188
- 2025-02-27 — expected epoch 348413
- 2025-02-28 — expected epoch 348638
- 2025-03-01 — expected epoch 348863
- 2025-10-18 — expected epoch 400838
- 2025-10-19 — expected epoch 401063

Every recovered date must satisfy the exact time/epoch/integrity rules above.

## Recovery PASS

ALTERNATE_PARQUET_READER_RECOVERY_PASS requires:
- 3/3 controls exact;
- 7/7 missing dates valid;
- exact expected epoch for all seven;
- no source/object substitution;
- no market or signal access.

If DuckDB cannot read one or more exact objects:
SOURCE_ACQUISITION_TECHNICAL_FAILURE.

If a control or epoch disagrees:
SOURCE_PROVENANCE_FAILURE.

## Stage-A consequence

A PASS permits splicing ONLY the seven recovered rows into the immutable 601-date original Stage-A corpus.

The aggregate must still prove 608/608 exact date geometry before emitting SOURCE_REPLICATION_PASS.

## Firewall

Source-only.
No signal evaluation.
No ETH/BTC price access.
No returns.
No PnL.
No source after 2026-08-31.
No market after 2026-09-08.
No live trading/orders/wallets/exchange mutation.
No main merge.
No post-outcome tuning.
