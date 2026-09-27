# ETH-STAKING-FLOW-001 — V3 STAGE-A DAILY + TRANSITION REMEDIATION V0.2.2

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Recover the exact seven missing Stage-A source dates using two official ethPandaOps Xatu CBT transformations that both derive from canonical_beacon_validators:

1. fct_validator_count_by_entity_by_status_daily
2. dim_validator_status

The daily table provides the validator-status population at the epoch immediately BEFORE UTC midnight for day D under its published intDiv epoch construction.

The frozen target remains the first canonical epoch at/after UTC midnight.

V0.2.2 bridges exactly one epoch by applying the actual validator status transitions observed at the frozen target epoch.

No economic rule changes.

## Frozen endpoints

Daily counts:
https://lab.ethpandaops.io/api/v1/mainnet/fct_validator_count_by_entity_by_status_daily

Transitions:
https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status

No alternate endpoint.

## Frozen geometry

Ethereum mainnet genesis timestamp:
1606824023

Epoch duration:
384 seconds

For date D with unix midnight M:

floor_epoch = floor((M - genesis) / 384)
floor_unix = genesis + floor_epoch * 384

target_epoch = ceil((M - genesis) / 384)
target_unix = genesis + target_epoch * 384

For the frozen dates, target_epoch = floor_epoch + 1.

The target is unchanged:
first canonical epoch at/after 00:00 UTC.

## Daily floor-state counts

For each date D query:
- day_start_date_eq=D
- status_eq=pending_queued
- page_size=10000

and separately:
- day_start_date_eq=D
- status_eq=active_exiting
- page_size=10000

Sum validator_count across all returned entities.

This is the published CBT daily table state at floor_epoch.

## Exact target-epoch transition set

Query dim_validator_status with:
- validator_index_gte=0
- epoch_eq=target_epoch
- page_size=10000
- order_by=validator_index,status

Complete pagination mandatory.

For every returned row require:
- epoch == target_epoch
- epoch_start_date_time == target_unix
- validator_index non-null
- status non-empty

If the same validator has more than one distinct new status at the same target epoch:
SOURCE_PROVENANCE_FAILURE.

## Previous status resolution

For every validator V appearing in the target-epoch transition set, query dim_validator_status with:
- validator_index_eq=V
- epoch_lt=target_epoch
- page_size=100
- order_by=epoch desc

Select exactly the latest prior lifecycle row.

If no prior row exists, previous status is treated as ABSENT_FROM_STATUS_POPULATION.

If multiple distinct statuses share the same latest prior epoch:
SOURCE_PROVENANCE_FAILURE.

## Exact delta rule

Initialize:
pending_target = pending_floor
exiting_target = exiting_floor

For each validator transition:
- if previous_status == pending_queued: pending_target -= 1
- if previous_status == active_exiting: exiting_target -= 1
- if new_status == pending_queued: pending_target += 1
- if new_status == active_exiting: exiting_target += 1

No other status name receives special handling.

This makes the adjustment depend only on the validator's actual prior and new statuses, not on assumed lifecycle paths.

Require final counts non-negative.

net_queue_target = pending_target - exiting_target.

## Mandatory controls

Before any missing date is accepted, reproduce exactly:

2025-02-24:
- target epoch 347738
- target unix 1740355415
- pending 0
- active_exiting 5
- net -5

2025-03-02:
- target epoch 349088
- target unix 1740873815
- pending 0
- active_exiting 0
- net 0

2025-10-17:
- target epoch 400613
- target unix 1760659415
- pending 48
- active_exiting 55209
- net -55161

3/3 exact required.

Any mismatch:
SOURCE_PROVENANCE_FAILURE.

## Seven frozen missing dates

Only after 3/3 controls exact:

- 2025-02-25 — target epoch 347963
- 2025-02-26 — target epoch 348188
- 2025-02-27 — target epoch 348413
- 2025-02-28 — target epoch 348638
- 2025-03-01 — target epoch 348863
- 2025-10-18 — target epoch 400838
- 2025-10-19 — target epoch 401063

## Splice gate

Legacy authority:
GitHub Actions run 35387477455.

Require:
- 601 valid legacy dates
- exactly the seven frozen missing dates absent
- 7/7 exact remediation rows
- exactly 608 final unique dates from 2025-01-01 through 2026-08-31
- exact target epoch/unix geometry on every final row
- deterministic daily-series SHA-256

Only the seven missing rows may be replaced/supplied by V0.2.2.

## Classification

SOURCE_REPLICATION_PASS iff all mandatory gates pass.

SOURCE_PROVENANCE_FAILURE for readable semantic/control/geometry inconsistency.

SOURCE_ACQUISITION_TECHNICAL_FAILURE for transport/schema/pagination failure.

## Firewall

Source-only.
No signal evaluation.
No threshold evaluation.
No ETH/BTC market data.
No returns/PnL.
No source after 2026-08-31.
No market after 2026-09-08.
No live trading/orders/wallets/exchange mutation.
No main merge.
No post-outcome tuning.

Stage B remains closed unless SOURCE_REPLICATION_PASS.
