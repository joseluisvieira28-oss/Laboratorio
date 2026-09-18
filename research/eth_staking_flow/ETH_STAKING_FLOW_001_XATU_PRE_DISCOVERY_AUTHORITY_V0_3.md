# ETH-STAKING-FLOW-001 — XATU CANONICAL SNAPSHOT MVE V0.3 — PRE-DISCOVERY AUTHORITY

Status: **FROZEN PRE-OUTCOME / SOURCE-DATA GATE ONLY**
Freeze date: 2026-09-18 UTC
Repository: `joseluisvieira28-oss/Laboratorio`
Branch: `eth-staking-flow-v0.3-xatu`

## Identity

Family: `ETH-STAKING-FLOW-001`
New MVE: **`ESF-NETQUEUE-XATU-7D-003`**

This is a new prospective MVE. It does not reopen, rewrite or rescue:
- V0.1 `ESF-NETQUEUE-7D-001` = `SOURCE_AUTH_BLOCKED`;
- V0.2 `ESF-NETQUEUE-SNAPSHOT-7D-002` = `DATA_FAILURE` (589/591, missing 2024-01-20 and 2024-01-21).

No ETH/BTC market outcome has been opened for V0.3 before this freeze.

## Economic mechanism

A large positive ETH validator net-entry queue-pressure state may represent stronger marginal demand to lock ETH than demand to exit, and may precede positive ETH returns.

Single source variable:

`net_queue_count_t = pending_queued_count_t - active_exiting_count_t`

No secondary source variable or filter is authorized.

## Canonical source

Public ethPandaOps Xatu Parquet:
- network: `mainnet`
- database: `default`
- table: `canonical_beacon_validators`
- partition column: `epoch_start_date_time`
- partition frequency: hourly
- base:
  `https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators/`

Required fields:
- `epoch`
- `epoch_start_date_time`
- `index`
- `status`

ClickHouse authenticated access is not part of this MVE. Public Parquet is the only authorized route.

## Frozen source window

Inclusive UTC dates:
**2023-04-12 through 2024-12-31**

Expected observations if complete: **630**.

For every date `YYYY-MM-DD`, only the exact public hour-0 object may be used:

`YYYY/M/D/0.parquet`

No other hour may be substituted if hour 0 is missing or malformed.

## Snapshot rule

For each UTC date:

1. Inspect the exact hour-0 partition.
2. Select the **minimum canonical `epoch_start_date_time` >= 00:00:00 UTC**.
3. That timestamp must be <= **00:06:24 UTC** (+32 slots).
4. Select the exact `epoch` corresponding to that timestamp.
5. Within that exact epoch, require one canonical row per validator `index`; duplicate validator indices fail closed.
6. `pending_queued_count` = number of rows whose exact `status` is `pending_queued`.
7. `active_exiting_count` = number of rows whose exact `status` is `active_exiting`.
8. If a status is absent from a complete canonical epoch, its count is zero. No forward/back fill or interpolation.

No balance/effective-balance/slashing value is part of the predictor.

## Source/Data Gate

PASS requires all:

- 630/630 exact UTC dates represented;
- 630/630 exact hour-0 Parquet paths accessible;
- required schema on every object;
- each date has a first canonical epoch in the +32-slot window;
- exact one-row-per-validator-index uniqueness in each selected epoch;
- non-negative integer counts for both statuses;
- zero duplicate dates;
- zero outside-window dates;
- raw URL/object metadata and deterministic daily source receipts preserved;
- no 2025/2026 source object requested;
- no ETH/BTC market prices, returns or PnL opened.

Allowed terminal states:
- `SOURCE_DATA_PASS`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `DATA_FAILURE`
- `PROVENANCE_FAILURE`
- `INSUFFICIENT_SAMPLE`

No source-stage result is `NO_EDGE`.

## Later Discovery rule — frozen now but dormant

Only after `SOURCE_DATA_PASS` and a separately authorized outcome opening:

- after at least 90 prior daily observations;
- signal when `net_queue_count_t` is at or above the trailing 90-observation 80th percentile, using only observations available through t;
- direction: **LONG ETH**;
- execution: next UTC daily open after t;
- holding period: 7 calendar days;
- overlapping positions prohibited;
- BASE round-trip cost: 10 bps;
- STRESS round-trip cost: 20 bps;
- no stop, target, leverage, short leg, BTC alternative, secondary filter, threshold sweep, horizon sweep or cost rescue.

## Frozen promotion gates

All required:
- provenance/leakage PASS;
- >=30 resolved non-overlapping events;
- mean NET10 > 0;
- PF NET10 > 1.0;
- one-sided stationary-bootstrap p(mean NET10 <= 0) <= 0.10;
- 2023 and 2024 calendar blocks both non-negative when each has >=5 events.

NET20 is fragility diagnostic only.

## Hard firewalls

Until a later explicit Discovery authorization:
- ETH price values: forbidden;
- BTC price values: forbidden;
- returns: forbidden;
- PnL/PF/win-rate/drawdown: forbidden;
- 2025/2026: forbidden;
- live trading/orders/wallets/exchange mutation: forbidden;
- alerts/webhooks: forbidden;
- merge to main: forbidden;
- post-outcome tuning: forbidden.
