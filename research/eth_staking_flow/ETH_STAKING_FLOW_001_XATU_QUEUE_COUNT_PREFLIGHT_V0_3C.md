# ETH-STAKING-FLOW-001 / ESF-NETQUEUE-XATU-7D-003 — QUEUE COUNT ENGINE PREFLIGHT V0.3C

Date: 2026-09-18
Status: **FROZEN BEFORE FIRST STATUS/QUEUE VALUE ACCESS / SOURCE-ONLY / OUTCOME-BLIND**

## Preconditions

- V0.3 authority frozen.
- V0.3A `SOURCE_FEASIBILITY_PASS`.
- V0.3B `XATU_FULL_COVERAGE_PASS`.
- V0.3B run: `35380646670`.
- canonical V0.3B artifact ID: `10561174603`.
- canonical V0.3B artifact digest:
  `sha256:090d2db70b1ef0e77c88a5433b2dc48cb25598e9e7be4ca776f28b0cd130ce30`.
- exact coverage: 630/630 HTTP PASS, 630/630 PAR1, 0 missing.

## Purpose

Validate the deterministic daily canonical-epoch extraction/count engine on the four pre-existing feasibility dates before scaling to all 630 dates.

This is the **first V0.3 phase allowed to open validator `status` values**. It still opens no ETH/BTC market outcome.

## Frozen dates

Exactly:
- 2023-04-12
- 2023-09-01
- 2024-06-15
- 2024-12-31

No date substitution after inspection.

## Exact extraction algorithm

For each exact hour-0 Parquet object:

1. Read Parquet metadata.
2. Let `T` be the minimum `epoch_start_date_time` represented in the object.
3. Require `T` in [00:00:00, 00:06:24] UTC for that date.
4. Select every row group whose `epoch_start_date_time` min/max statistics can contain `T`.
5. Read only columns:
   - `epoch`
   - `epoch_start_date_time`
   - `index`
   - `status`
6. Filter rows exactly to `epoch_start_date_time == T`.
7. Require exactly one epoch value in the filtered rows.
8. Require validator `index` non-null and unique; any duplicate index is provenance failure.
9. `pending_queued_count` = exact count of status `pending_queued`.
10. `active_exiting_count` = exact count of status `active_exiting`.
11. `net_queue_count` = pending minus exiting.
12. Preserve only aggregate daily receipt values; do not persist validator-level rows.

A legitimately absent target status in a complete selected epoch counts as zero.

## PASS

`QUEUE_COUNT_ENGINE_PASS` requires all four dates:
- temporal rule PASS;
- >=1 selected row group;
- >=1 filtered validator row;
- one exact epoch;
- zero duplicate/null validator indices;
- integer non-negative pending/exiting counts;
- deterministic net count arithmetic.

## Next gate

Only PASS permits full 630-date V0.3D reconstruction using the exact same algorithm, sharded by month.

## Firewalls

No ETH/BTC prices, returns, PnL, signal threshold evaluation, event counting, 2025/2026, trading/orders/wallets/exchange mutation, main merge.
