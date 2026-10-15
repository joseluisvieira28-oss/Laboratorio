# ETH-STAKING-FLOW-001 — XATU PUBLIC SOURCE RECOVERY ADDENDUM V0.2

Date: 2026-09-18
Branch: `eth-staking-flow-v0.1`
Status: **FROZEN BEFORE FIRST XATU PROBE / SOURCE-ONLY / OUTCOME-BLIND**

## Historical parent preserved

The V0.1 Source/Data Gate remains historically `SOURCE_AUTH_BLOCKED`.
It is not NO_EDGE and Discovery was never executed.

Frozen MVE remains unchanged:
- lab: `ETH-STAKING-FLOW-001`
- MVE: `ESF-NETQUEUE-7D-001`
- variable: `pending_queued_count - active_exiting_count`
- source window: 2023-04-12 through 2024-12-31
- later Discovery rule, direction, 7-day horizon, costs and promotion gates remain unchanged and dormant.

V0.2 changes only the candidate historical source route.

## New candidate source

Public ethPandaOps Xatu canonical beacon dataset:
- table: `canonical_beacon_validators`
- public parquet root:
  `https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators/`

Current public documentation identifies `canonical_beacon_validators` as a canonical beacon table and documents public Parquet access for Xatu. Public research using this table demonstrates epoch snapshots with fields including validator `status`, `epoch`, `epoch_start_date_time`, lifecycle epochs and validator index.

No current-state value may be substituted for a historical partition.

## Exact feasibility probes

Before attempting the full 630-day source series, probe exactly four protected-safe UTC dates:

- 2023-04-12
- 2023-09-01
- 2024-06-15
- 2024-12-31

Frozen expected daily URL shape:
`.../canonical_beacon_validators/YYYY/M/D.parquet`
using non-zero-padded month/day.

For each date the probe may inspect only:
- HTTP availability and object metadata;
- Parquet schema and column names/types;
- min/max epoch and epoch_start_date_time;
- distinct epoch count;
- distinct validator status labels;
- row count only if obtainable through columnar metadata/query;
- whether `pending_queued` and `active_exiting` are represented.

The probe MUST NOT read or query 2025/2026 partitions.

## Required semantic columns

The source-feasibility pass requires enough point-in-time fields to identify validator status at the snapshot, including at minimum:

- `epoch`
- `epoch_start_date_time`
- `index`
- `status`

Lifecycle columns may be recorded for provenance if present but are not required to pass this first probe.

## Temporal adequacy rule

The eventual original snapshot clock is preserved:
first canonical consensus state at or after 00:00:00 UTC, bounded to +32 slots.

V0.2 feasibility PASS requires each deterministic probe day to contain at least one canonical epoch snapshot whose `epoch_start_date_time` falls in [00:00:00, 00:06:24] UTC.

This probe may prove such an epoch exists. It must not yet build the 630-day net-queue series.

## Classification

Permitted terminal states:
- `XATU_SOURCE_FEASIBILITY_PASS`
- `XATU_SOURCE_PATH_NOT_FOUND`
- `XATU_SCHEMA_INSUFFICIENT`
- `XATU_TEMPORAL_ALIGNMENT_FAIL`
- `XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `PROVENANCE_FAILURE`

None is an edge verdict.

## Next gate

Only `XATU_SOURCE_FEASIBILITY_PASS` permits a separately frozen full 2023-04-12..2024-12-31 acquisition/reconstruction gate using the same Xatu route.

Discovery remains forbidden until:
1. full source/data reconstruction passes;
2. the original final pre-Discovery contract is re-bound to the new canonical source receipts;
3. a separate authorization opens outcomes.

## Firewalls

Still forbidden:
- ETH prices;
- BTC prices;
- returns;
- PnL/PF/win-rate/drawdown;
- 2025/2026 scientific data;
- threshold/horizon/sign/cost changes;
- live trading, orders, wallets, exchange mutation, alerts/webhooks;
- merge to main.
