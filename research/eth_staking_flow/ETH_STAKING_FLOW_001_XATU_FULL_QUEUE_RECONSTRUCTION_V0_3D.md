# ETH-STAKING-FLOW-001 / ESF-NETQUEUE-XATU-7D-003 — FULL QUEUE RECONSTRUCTION V0.3D

Date: 2026-09-18
Status: **FROZEN / DORMANT UNTIL EXACT V0.3C PASS / SOURCE-ONLY / OUTCOME-BLIND**

## Activation

V0.3D may execute only if GitHub Actions run **35380959352** produces:
`classification = QUEUE_COUNT_ENGINE_PASS`

for the exact four-date V0.3C engine preflight.

Any other classification keeps V0.3D dormant.

## Upstream source authority

- V0.3 pre-Discovery authority frozen before queue values.
- V0.3A = SOURCE_FEASIBILITY_PASS.
- V0.3B = XATU_FULL_COVERAGE_PASS, 630/630.
- V0.3B canonical run = 35380646670.
- V0.3B canonical artifact digest =
  `sha256:090d2db70b1ef0e77c88a5433b2dc48cb25598e9e7be4ca776f28b0cd130ce30`.

## Purpose

Reconstruct the exact daily source series for every frozen date without opening any ETH/BTC market outcome.

## Frozen population

UTC 2023-04-12..2024-12-31 inclusive, exactly 630 dates.

Only:
`canonical_beacon_validators/YYYY/M/D/0.parquet`

## Per-date algorithm

Byte/semantic-identical to V0.3C:

1. Determine minimum `epoch_start_date_time` from Parquet row-group metadata.
2. Require it within [00:00:00, 00:06:24] UTC.
3. Read only row groups whose timestamp stats can contain that exact time.
4. Read only columns `epoch`, `epoch_start_date_time`, `index`, `status`.
5. Filter exactly to selected timestamp.
6. Require one exact epoch.
7. Require non-null unique validator indices.
8. Count exact `pending_queued`.
9. Count exact `active_exiting`.
10. Compute `net_queue_count = pending_queued - active_exiting`.
11. Persist only daily aggregate source records, never validator-level rows.

No missing date, failed date, alternate hour or alternate source may be dropped/replaced.

## Sharding

Exactly 21 calendar-month shards, using the same date partitioning as V0.3B:
- partial 2023-04 from day 12;
- then each complete month;
- through 2024-12.

Every shard preserves per-date failures and terminates non-PASS if any included date fails.

## Canonical aggregate PASS

`SOURCE_DATA_PASS` requires:
- exactly 21 shard receipts;
- every shard PASS;
- exactly 630 unique dates;
- no missing/outside/duplicate dates;
- all selected times within +32 slots;
- one epoch per date;
- unique validator index population on every date;
- pending/exiting counts integer and non-negative;
- deterministic daily source-series SHA256;
- protected-period firewall PASS.

The aggregate may report source coverage/count integrity only.
It must NOT evaluate:
- trailing percentile;
- signal days;
- event count;
- future ETH return;
- PnL/PF/win rate/drawdown;
- 2025/2026.

## Next gate

Only SOURCE_DATA_PASS permits binding a separately-authorized one-shot Discovery runner to the frozen V0.3 authority.

Discovery is NOT authorized by V0.3D itself.

## Firewalls

No ETH/BTC price data, returns, PnL, signal evaluation, 2025/2026, trading/orders/wallets/exchange mutation, alerts/webhooks, main merge or post-outcome tuning.
