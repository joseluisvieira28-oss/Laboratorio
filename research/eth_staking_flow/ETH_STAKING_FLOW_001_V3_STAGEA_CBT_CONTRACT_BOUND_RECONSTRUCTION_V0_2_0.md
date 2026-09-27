# ETH-STAKING-FLOW-001 — V3 STAGE-A CBT CONTRACT-BOUND RECONSTRUCTION V0.2.0

Date frozen: 2026-09-27
Status: FROZEN BEFORE FULL CBT ACQUISITION / SOURCE-ONLY / OUTCOME-BLIND

## Parent evidence

V0.1.9 API contract probe:
- run: 36313857671
- classification: CBT_API_CONTRACT_PASS
- usable endpoint: https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status
- exact validator IDs 0,1,2 all returned one valid lifecycle row
- row field: dim_validator_status
- required fields present:
  validator_index, status, epoch, epoch_start_date_time, activation_epoch, exit_epoch

The alternative root lab path and direct CBT host returned HTTP 404 and are excluded from this reconstruction.

## Purpose

Re-run the already-authorized V0.1.5 sparse lifecycle reconstruction against the now-proven REST contract.

This changes transport binding only. It does not change:
- target date range;
- target epoch geometry;
- queue definitions;
- lifecycle inequalities;
- controls;
- legacy overlap authority;
- market instrument;
- signal;
- threshold;
- direction;
- holding period;
- costs;
- promotion policy.

## Frozen source

Only:
https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status

No alternate endpoint is permitted in this run.

## Frozen sparse lifecycle queries

For pending_queued:
- validator_index_gte=0
- status_eq=pending_queued
- epoch_lte=472163
- activation_epoch_gte=335588
- page_size=10000
- order_by=validator_index,epoch

For active_exiting:
- validator_index_gte=0
- status_eq=active_exiting
- epoch_lte=472163
- exit_epoch_gte=335588
- page_size=10000
- order_by=validator_index,epoch

Complete pagination is mandatory.

## Frozen state-count identities

At target epoch E:

pending_queued_count(E) =
count(rows where transition_epoch <= E AND activation_epoch > E)

active_exiting_count(E) =
count(rows where transition_epoch <= E AND exit_epoch > E)

net_queue_count(E) =
pending_queued_count(E) - active_exiting_count(E)

These are unchanged from V0.1.5A.

## Frozen target geometry

Range:
2025-01-01 through 2026-08-31 inclusive.

Exactly 608 dates.

Ethereum mainnet genesis:
1606824023

Epoch duration:
384 seconds.

For date D:
target_epoch = ceil((unix_midnight(D)-1606824023)/384)
target_unix = 1606824023 + target_epoch*384

No nearest epoch, interpolation, adjacent-day substitution or current-state substitution.

## Mandatory controls

Exact:

2025-02-24:
epoch 347738
unix 1740355415
pending 0
active_exiting 5
net -5

2025-03-02:
epoch 349088
unix 1740873815
pending 0
active_exiting 0
net 0

2025-10-17:
epoch 400613
unix 1760659415
pending 48
active_exiting 55209
net -55161

3/3 exact required.

## Legacy overlap gate

Immutable authority:
GitHub Actions run 35387477455.

Collect its 20 monthly Stage-A shard artifacts.

The reconstructed ledger must match all 601 valid legacy dates exactly on:
- selected_epoch
- selected_unix_time
- pending_queued_count
- active_exiting_count
- net_queue_count

Required:
601/601 exact.

## Seven missing dates

Must be materialized exactly:
- 2025-02-25 epoch 347963
- 2025-02-26 epoch 348188
- 2025-02-27 epoch 348413
- 2025-02-28 epoch 348638
- 2025-03-01 epoch 348863
- 2025-10-18 epoch 400838
- 2025-10-19 epoch 401063

## Stage-A terminal classifications

SOURCE_REPLICATION_PASS only if ALL:
- both sparse queries return usable rows;
- pagination terminates cleanly;
- lifecycle integrity passes;
- 3/3 controls exact;
- 601/601 legacy overlap exact;
- 7/7 missing dates reconstructed;
- 608/608 final unique dates;
- no source date after 2026-08-31;
- deterministic source hashes emitted.

Any readable semantic mismatch:
SOURCE_PROVENANCE_FAILURE.

Any transport/query/pagination/acquisition failure:
SOURCE_ACQUISITION_TECHNICAL_FAILURE.

## Stage-B firewall

Stage B remains CLOSED unless this exact run emits SOURCE_REPLICATION_PASS.

Forbidden here:
- ETH/BTC price access;
- signal evaluation;
- threshold evaluation;
- returns/PnL;
- 2026 source after 2026-08-31;
- trading/orders/wallets/exchange mutation;
- main merge;
- post-outcome tuning.
