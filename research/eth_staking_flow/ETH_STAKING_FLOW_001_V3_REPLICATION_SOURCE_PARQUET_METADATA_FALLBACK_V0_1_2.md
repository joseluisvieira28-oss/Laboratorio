# ETH-STAKING-FLOW-001 — V3 REPLICATION SOURCE PARQUET-METADATA FALLBACK V0.1.2

Date: 2026-09-19
Branch: `eth-staking-flow-v0.3-discovery`
Status: **FROZEN BEFORE EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

## Trigger evidence

The canonical V3 replication-source run `35387477455` materialized 601/608 daily source observations. Seventeen of twenty monthly shards passed. The three failed shards were `202502`, `202503`, and `202510`.

Transport recovery V0.1.1 run `35394126480` retried the exact same daily URLs with bounded backoff. It confirmed that the remaining seven failures are deterministic Parquet metadata-availability failures, not HTTP/transport failures:

- 2025-02-25: `no timestamp row-group stats`
- 2025-02-26: `no timestamp row-group stats`
- 2025-02-27: `no timestamp row-group stats`
- 2025-02-28: `no timestamp row-group stats`
- 2025-03-01: `no timestamp row-group stats`
- 2025-10-18: `no timestamp row-group stats`
- 2025-10-19: `no timestamp row-group stats`

The Parquet objects exist and are readable. No signal, ETH/BTC market price, return or PnL was opened.

## Exact permitted remediation

The scientific source rule remains unchanged:

**select the first canonical validator snapshot at or after 00:00:00 UTC, bounded to +32 slots, then count exact `pending_queued` and `active_exiting` validator statuses with unique validator index.**

V0.1.2 may change only how the exact first timestamp is located when the Parquet file lacks row-group min/max statistics for `epoch_start_date_time`.

Algorithm:

1. Run the original V0.1 reconstruction unchanged.
2. If and only if it fails with the exact condition `no timestamp row-group stats`, open the same Parquet URL and same `epoch_start_date_time` column.
3. For each row group, compute actual minimum and maximum timestamp values from the column values themselves.
4. Select `T = min(all row-group actual minima)`.
5. Apply the unchanged UTC-day and +32-slot bound.
6. Read all row groups whose actual timestamp range contains `T`.
7. Apply the unchanged exact equality filter `epoch_start_date_time == T`.
8. Apply the unchanged unique validator-index, single-epoch and status-count checks.
9. Emit the same daily fields and mark only that `timestamp_locator = COLUMN_VALUE_FALLBACK_NO_ROWGROUP_STATS`.

No nearest-time substitution, interpolation, adjacent-day substitution, later timestamp selection, current-state substitution, or missing-day deletion is allowed.

## Prospective equivalence QA

Before the seven failed dates may be accepted, V0.1.2 must prove semantic equivalence on deterministic normal control days where row-group statistics exist:

- 2025-02-24
- 2025-03-02
- 2025-10-17

For each control day, the original metadata-statistics route and the forced column-value route must agree exactly on:

- selected Unix timestamp;
- selected epoch;
- validator row count;
- unique validator count;
- pending_queued count;
- active_exiting count;
- net_queue_count.

Any mismatch = **PROVENANCE_FAILURE / STOP**.

## Scope

Recovery may rerun only the three frozen monthly shards:
`202502`, `202503`, `202510`.

The aggregate must continue to use:
- 17 original `SHARD_PASS` receipts from run `35387477455`;
- three V0.1.2 recovered monthly receipts.

Original failed receipts and V0.1.1 failed receipts remain immutable history.

## Stage-A pass rule unchanged

`SOURCE_REPLICATION_PASS` still requires exactly 608 unique daily source observations from 2025-01-01 through 2026-08-31, zero missing/duplicate/outside dates, exact source cutoff, and no market outcomes.

Only `SOURCE_REPLICATION_PASS` may release the already-frozen Stage-B independent outcome replication. This amendment does not authorize Stage B by itself.

## Firewalls unchanged

Forbidden throughout V0.1.2:
- signal evaluation;
- threshold evaluation;
- ETH/BTC prices;
- returns;
- PnL;
- source dates after 2026-08-31;
- market dates;
- live trading;
- orders;
- wallets;
- exchange mutation;
- alerts/webhooks;
- main merge;
- post-outcome tuning.

This is a source-encoding compatibility remediation only. It changes no hypothesis, date population, threshold, direction, asset, horizon, costs, overlap rule, sample gate or promotion rule.
