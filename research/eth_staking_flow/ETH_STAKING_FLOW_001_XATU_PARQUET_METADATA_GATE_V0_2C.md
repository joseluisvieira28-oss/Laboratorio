# ETH-STAKING-FLOW-001 — XATU PARQUET METADATA GATE V0.2C

Date: 2026-09-18
Branch: `eth-staking-flow-v0.1`
Status: **FROZEN BEFORE METADATA ACCESS / SOURCE-ONLY / OUTCOME-BLIND**

## Upstream

V0.2B HTTP transport PASS:
- run: `35379954338`
- exact four hour-0 objects;
- 4/4 HTTP 206;
- 4/4 prefix `PAR1`;
- no validator rows opened.

## Purpose

Prove the exact public Parquet objects expose the columns and temporal partition semantics required by the original ESF source contract without scanning validator values.

## Exact objects

Unchanged:
- 2023/4/12/0.parquet
- 2023/9/1/0.parquet
- 2024/6/15/0.parquet
- 2024/12/31/0.parquet

Table: `canonical_beacon_validators`.

## Allowed metadata

Using HTTP range reads only through a Parquet metadata reader, inspect:
- Arrow/Parquet schema names and types;
- file row count;
- row-group count;
- row-group statistics only for `epoch_start_date_time` and `epoch`;
- file byte size from the remote filesystem.

Do NOT read validator-level column values, status labels, balances or lifecycle values in this gate.

## Required schema

All four objects must contain:
- `epoch`
- `epoch_start_date_time`
- `index`
- `status`

## Temporal gate

For every probe object, Parquet metadata statistics must establish that the earliest `epoch_start_date_time` represented in the hour-0 partition falls in:

`[00:00:00 UTC, 00:06:24 UTC]`

on its frozen date.

If metadata statistics are absent, classify `XATU_METADATA_INSUFFICIENT`; do not scan rows to rescue this exact gate.

## PASS

`XATU_PARQUET_METADATA_PASS` requires all four:
- exact paths accessible;
- required schema complete;
- row_count > 0;
- row_group_count > 0;
- timestamp metadata available;
- earliest timestamp inside the frozen +32-slot window.

## Terminal states

- XATU_PARQUET_METADATA_PASS
- XATU_SCHEMA_INSUFFICIENT
- XATU_METADATA_INSUFFICIENT
- XATU_TEMPORAL_ALIGNMENT_FAIL
- XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE
- PROVENANCE_FAILURE

No terminal state is an economic verdict.

## Firewalls

No status values/counts, net queue, ETH/BTC prices, returns, PnL, 2025/2026 access, tuning, trading, wallet/exchange mutation, alerts/webhooks or main merge.
