# ETH-STAKING-FLOW-001 — V3 STAGE-A CBT TRANSITION-LEDGER SOURCE REMEDIATION V0.1.5

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND
Parent state: V3 Stage-A SOURCE_ACQUISITION_TECHNICAL_FAILURE

## Purpose

Recover the exact V3 Stage-A validator queue source state without changing the frozen scientific signal.

The prior Xatu canonical Parquet route materialized 601/608 dates. Exactly seven dates remain unavailable through the original daily objects. The Beacon-state V0.1.4 endpoint remediation also failed technically.

V0.1.5 introduces a distinct SOURCE ARCHITECTURE only. It does not alter the signal, date population, threshold, direction, horizon, costs, overlap rule, or promotion policy.

## New source architecture

Source model:
ethPandaOps Xatu CBT `dim_validator_status`.

Model semantics:
- derived from `canonical_beacon_validators`;
- one row per (validator_index, status);
- records the first epoch at which that validator was observed in that lifecycle status.

Candidate public transports, frozen before probe:
1. Lab proxy:
   https://lab.ethpandaops.io/api/v1/mainnet
2. Direct CBT API:
   https://cbt-api-mainnet.primary.production.platform.ethpandaops.io/api/v1

These are transport alternatives to the same CBT model and are NOT counted as independent scientific sources.

## Exact frozen target semantics

UNCHANGED from V0.1–V0.1.4:

For each UTC date, target the first canonical epoch boundary at or after 00:00:00 UTC.

Ethereum mainnet genesis timestamp:
1606824023.

Epoch duration:
384 seconds.

For date D:
target_epoch = ceil((unix_midnight(D) - genesis_timestamp) / 384)

target_unix = genesis_timestamp + target_epoch * 384.

The source state is valid only if the reconstructed state is exactly at target_epoch / target_unix.

No previous-epoch daily aggregate, nearest-time, adjacent-day, interpolation, or current-state substitution is permitted.

## Frozen control dates

The new reconstruction MUST reproduce exactly:

2025-02-24:
- epoch 347738
- unix 1740355415
- pending_queued 0
- active_exiting 5
- net_queue -5

2025-03-02:
- epoch 349088
- unix 1740873815
- pending_queued 0
- active_exiting 0
- net_queue 0

2025-10-17:
- epoch 400613
- unix 1760659415
- pending_queued 48
- active_exiting 55209
- net_queue -55161

Any mismatch = SOURCE_PROVENANCE_FAILURE / STOP.

## Exact seven missing dates

Only these previously missing dates require new materialization:
- 2025-02-25 — epoch 347963
- 2025-02-26 — epoch 348188
- 2025-02-27 — epoch 348413
- 2025-02-28 — epoch 348638
- 2025-03-01 — epoch 348863
- 2025-10-18 — epoch 400838
- 2025-10-19 — epoch 401063

## Transition-ledger reconstruction

Fetch CBT transition rows with:
- validator_index >= 0;
- epoch <= 401063;
- complete pagination;
- no silent truncation.

For target epoch E:

1. Include only transition rows with epoch <= E.
2. For each validator_index, select the row with maximum epoch.
3. If a validator has more than one DISTINCT status at the same maximum epoch, fail as SOURCE_PROVENANCE_FAILURE.
4. The selected status is the reconstructed validator status at E.
5. Count exactly:
   - status == pending_queued
   - status == active_exiting
6. net_queue_count = pending_queued - active_exiting.

No validator may be imputed or dropped because of a status value.

## Full 601-date equivalence gate

The original run #35387477455 produced 601 valid daily source observations and seven missing dates.

Before any newly recovered date may be admitted, V0.1.5 MUST compare the transition-ledger reconstruction against ALL 601 previously valid observations.

For every overlapping date require exact equality on:
- date;
- selected_epoch;
- selected_unix_time;
- pending_queued_count;
- active_exiting_count;
- net_queue_count.

Equivalence requirement:
601 / 601 exact.

600/601 is FAIL.
No tolerance exists.

The original run artifacts remain immutable authority for this equivalence test.

## Stage-A PASS gate

Only if:
- endpoint/schema probe PASS;
- complete transition ledger acquisition PASS;
- 3/3 frozen controls exact;
- 601/601 historical overlap exact;
- seven missing dates reconstructed;
- final daily ledger = exactly 608 unique dates from 2025-01-01 through 2026-08-31;
- no date outside the frozen range;
- no duplicate date;
- exact target epoch/time geometry on every date;

may the source classification become:

SOURCE_REPLICATION_PASS.

Otherwise:
- transport/schema/acquisition failure => SOURCE_ACQUISITION_TECHNICAL_FAILURE;
- control or overlap mismatch => SOURCE_PROVENANCE_FAILURE.

## Stage-B firewall

V0.1.5 is SOURCE ONLY.

Forbidden:
- signal evaluation;
- threshold evaluation;
- ETH/BTC price access;
- returns;
- PnL;
- market dates;
- source date after 2026-08-31;
- live trading;
- orders;
- wallets;
- exchange mutation;
- main merge;
- post-outcome tuning.

Stage B remains CLOSED until and unless the exact V3 Stage-A aggregate emits SOURCE_REPLICATION_PASS.
