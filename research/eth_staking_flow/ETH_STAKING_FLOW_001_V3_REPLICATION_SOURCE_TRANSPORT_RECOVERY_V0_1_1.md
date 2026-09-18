# ETH-STAKING-FLOW-001 — V3 REPLICATION SOURCE TRANSPORT RECOVERY V0.1.1

Date: 2026-09-18
Branch: `eth-staking-flow-v0.3-discovery`
Status: **FROZEN BEFORE RECOVERY EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

## Trigger

Canonical V3 replication-source run `35387477455` executed the frozen 608-day source window
from 2025-01-01 through 2026-08-31.

Seventeen of twenty monthly shards completed `SHARD_PASS`.

Exactly three monthly shards terminated as `SOURCE_ACQUISITION_TECHNICAL_FAILURE`:

- `202502`: 24/28 dates materialized; 4 source-acquisition errors.
- `202503`: 30/31 dates materialized; 1 source-acquisition error.
- `202510`: 29/31 dates materialized; 2 source-acquisition errors.

The aggregate therefore emitted `SOURCE_REPLICATION_TECHNICAL_FAILURE`.

No signal, market price, return or PnL was opened by that run.

## Exact remediation

Recovery V0.1.1 may rerun **only** the three failed monthly shards above.

For each deterministic daily Xatu Parquet URL, V0.1.1 may retry the exact same
`reconstruct_day(date)` source request when the failure is transport-like.

Allowed recovery:
- exact same URL and day;
- exact same columns;
- exact same row-group timestamp-statistic selection;
- exact same +32-slot limit;
- exact same validator uniqueness checks;
- exact same pending_queued / active_exiting counts;
- maximum 5 attempts per day;
- bounded deterministic backoff: 2, 4, 8, 16 seconds.

Semantic/schema/provenance errors are not changed, filtered or reinterpreted.

## Aggregate rule

The recovery aggregate must use:

- the 17 original `SHARD_PASS` receipts from run `35387477455`;
- the 3 V0.1.1 recovery receipts for `202502`, `202503`, `202510`.

The three original failed shard receipts remain immutable technical history and are not deleted.

The canonical V0.1 aggregate implementation remains unchanged and must receive
exactly 20 selected shard receipts after deterministic replacement of only the
three technical failures.

## Firewalls

Still forbidden throughout source recovery:

- signal evaluation;
- threshold evaluation;
- ETH/BTC market prices;
- returns;
- PnL;
- 2026 data after 2026-08-31;
- live trading;
- orders/wallets/exchange mutation;
- main merge;
- post-outcome tuning.

Only a canonical `SOURCE_REPLICATION_PASS` may open the unchanged-rule independent
replication outcome stage already frozen by the V3 authority.
