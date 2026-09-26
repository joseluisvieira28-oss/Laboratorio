# ETH-STAKING-FLOW-001 — XATU HOURLY PARTITION ERRATUM V0.2A

Date: 2026-09-18
Branch: `eth-staking-flow-v0.1`
Status: **FROZEN BEFORE CORRECTED TRANSPORT PROBE / SOURCE-ONLY / OUTCOME-BLIND**

## Finding

The first Xatu feasibility probe V0.2 used the daily path shape:
`canonical_beacon_validators/YYYY/M/D.parquet`.

All four frozen dates returned HTTP 404.

After that failure, the official `ethpandaops/xatu-data` repository was inspected. Its public Parquet documentation states:

- table: `canonical_beacon_validators`
- partition column: `epoch_start_date_time`
- partition frequency: **hourly**
- datetime hourly URL shape: `YYYY/M/D/H.parquet`

The official ClickHouse schema also confirms the required source fields:
`epoch`, `epoch_start_date_time`, `index`, `status`, plus lifecycle epoch fields.

This is a source-path correction discovered before any market outcome or Discovery access.

## Corrected deterministic probe

Preserve the exact four V0.2 dates:
- 2023-04-12
- 2023-09-01
- 2024-06-15
- 2024-12-31

For each date request only the UTC hour-0 partition:
`.../canonical_beacon_validators/YYYY/M/D/0.parquet`.

No alternate hour, date, table or network may be substituted after result inspection.

## Semantics and gates unchanged

Required columns:
- epoch
- epoch_start_date_time
- index
- status

Temporal adequacy:
at least one canonical epoch snapshot at or after 00:00:00 UTC and no later than +32 slots (00:06:24 UTC) on each probe date.

May inspect only transport metadata, Parquet schema, epoch/time coverage, status labels and structural row/epoch counts.

## Classification

Permitted:
- XATU_SOURCE_FEASIBILITY_PASS
- XATU_SOURCE_PATH_NOT_FOUND
- XATU_SCHEMA_INSUFFICIENT
- XATU_TEMPORAL_ALIGNMENT_FAIL
- XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE
- PROVENANCE_FAILURE

V0.2 remains preserved as a failed daily-path transport attempt and is not rewritten.

## Firewalls

No ETH/BTC prices, returns, PnL, 2025/2026 scientific data, tuning, trading, orders, wallets, exchange mutation, alerts/webhooks or main merge.
