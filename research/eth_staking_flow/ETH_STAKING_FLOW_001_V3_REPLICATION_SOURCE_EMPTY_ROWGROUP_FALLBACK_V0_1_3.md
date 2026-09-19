# ETH-STAKING-FLOW-001 — V3 REPLICATION SOURCE EMPTY-ROWGROUP FALLBACK V0.1.3

Date: 2026-09-19
Branch: `eth-staking-flow-v0.3-discovery`
Status: **FROZEN BEFORE EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

## Trigger evidence

V0.1.2 equivalence QA passed on the three predeclared normal control days, but the seven target dates remained source-technical failures.

The exact deterministic failure exposed by run `35438864217` is not missing HTTP transport and not a scientific sample failure. The column-value fallback reached the correct same-day Parquet objects, then aborted because at least one physical row group returned an empty `epoch_start_date_time` column:

`RuntimeError: row group 0: empty epoch_start_date_time`.

Affected dates remain exactly:
- 2025-02-25
- 2025-02-26
- 2025-02-27
- 2025-02-28
- 2025-03-01
- 2025-10-18
- 2025-10-19

No signal, market price, return or PnL has been opened.

## Exact permitted remediation

The frozen scientific source rule remains unchanged:

**select the first canonical validator snapshot at or after 00:00:00 UTC, bounded to +32 slots, then count exact pending_queued and active_exiting statuses with unique validator index.**

V0.1.3 changes only physical Parquet row-group handling inside the already-authorized V0.1.2 column-value fallback.

For each row group in the same frozen daily Parquet object:

1. Read only `epoch_start_date_time`.
2. If the row group contains zero rows / zero non-null timestamp values, classify that physical row group as `EMPTY_ROWGROUP_SKIPPED` and exclude it from min/max construction.
3. Any non-empty row group containing null timestamp values remains fail-closed.
4. For every non-empty valid row group, compute actual timestamp min/max exactly as V0.1.2.
5. Select `T = min(all valid row-group minima)`.
6. Apply the unchanged UTC-day and +32-slot bound.
7. Read every non-empty row group whose timestamp range contains T.
8. Apply the unchanged exact equality filter and validator uniqueness/status-count checks.

An empty physical row group contributes no observations and therefore cannot determine the first canonical snapshot. Skipping it is an encoding/transport compatibility correction only.

Forbidden:
- skipping a non-empty row group;
- skipping null timestamp values inside a non-empty row group;
- adjacent-day substitution;
- nearest-time substitution;
- interpolation;
- later-time substitution;
- changing any date, threshold, signal, direction, asset, horizon, split or promotion gate.

## Scope

Only shards `202502`, `202503`, `202510` may execute.

The final aggregate must reuse the same 17 original passing receipts and replace only the three technical-failure receipts if V0.1.3 returns `SHARD_PASS`.

## Equivalence and lineage

The existing V0.1.2 normal-day equivalence QA remains required and preserved.

V0.1.3 must additionally report:
- physical row-group count;
- empty row-groups skipped;
- non-empty row-groups used for timestamp range construction;
- the exact seven fallback dates.

Stage-A pass remains exactly 608 unique dates through 2026-08-31.

## Firewalls

Still forbidden:
- signal evaluation;
- market prices;
- returns;
- PnL;
- dates after 2026-08-31;
- live trading/orders/wallets/exchange mutation;
- main merge;
- post-outcome tuning.

Only `SOURCE_REPLICATION_PASS` may release the separately frozen Stage-B independent replication.
