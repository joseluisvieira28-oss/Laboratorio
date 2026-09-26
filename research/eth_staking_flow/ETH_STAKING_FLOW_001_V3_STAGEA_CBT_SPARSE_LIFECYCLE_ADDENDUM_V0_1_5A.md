# ETH-STAKING-FLOW-001 — V3 STAGE-A CBT SPARSE LIFECYCLE RECONSTRUCTION ADDENDUM V0.1.5A

Date frozen: 2026-09-27
Parent: ETH_STAKING_FLOW_001_V3_STAGEA_CBT_TRANSITION_SOURCE_REMEDIATION_V0_1_5
Status: FROZEN BEFORE FULL CBT ACQUISITION / SOURCE-ONLY / OUTCOME-BLIND

## Clarification of acquisition stages

The lightweight V0.1.5 API/schema probe is permitted to inspect transition rows only through epoch 401063 because its sole purpose is transport/schema feasibility for the three controls and seven missing dates.

The FULL Stage-A reconstruction covers the entire frozen source range:

2025-01-01 through 2026-08-31 inclusive.

Target-epoch geometry:
- first target epoch: 335588
- first target unix: 1735689815
- last target epoch: 472163
- last target unix: 1788134615
- exact expected dates: 608.

## Sparse lifecycle reconstruction

A full download of every validator status transition is unnecessary.

For `pending_queued`, acquire only CBT `dim_validator_status` rows satisfying:
- validator_index >= 0;
- status == pending_queued;
- epoch <= 472163;
- activation_epoch >= 335588.

For `active_exiting`, acquire only rows satisfying:
- validator_index >= 0;
- status == active_exiting;
- epoch <= 472163;
- exit_epoch >= 335588.

Complete pagination is mandatory.

The required primary-key guard is satisfied only by the non-restrictive `validator_index_gte=0`; it is not a scientific filter.

## State-count identities

At target epoch E:

pending_queued_count(E) =
count(rows where pending_transition_epoch <= E AND activation_epoch > E)

active_exiting_count(E) =
count(rows where active_exiting_transition_epoch <= E AND exit_epoch > E)

net_queue_count(E) = pending_queued_count(E) - active_exiting_count(E).

These inequalities are frozen before acquisition.

A row relevant to the frozen interval with null activation_epoch (pending_queued) or null exit_epoch (active_exiting) is PROVENANCE_FAILURE.

For each status dataset:
- validator_index must be unique;
- duplicate validator_index rows fail closed;
- lifecycle end epoch must be >= transition epoch;
- acquisition must terminate with an empty next_page_token;
- repeated pagination token or silent truncation fails closed.

## Provenance hashes

For each acquired status dataset create a deterministic SHA-256 over rows sorted by:
validator_index, epoch.

Canonical hashed fields:
- validator_index
- status
- epoch
- epoch_start_date_time
- activation_epoch
- exit_epoch.

Raw validator-level rows need not be committed to git if acquisition counts and deterministic hashes are durably preserved.

## Legacy overlap authority

Run #35387477455 artifacts are immutable comparison authority.

Collect every `daily_source_records` entry from the 20 monthly shard artifacts.

Expected:
- exactly 601 unique valid dates;
- exactly the seven previously frozen missing dates absent.

V0.1.5 reconstructed values must match 601/601 exactly on:
- selected_epoch;
- selected_unix_time;
- pending_queued_count;
- active_exiting_count;
- net_queue_count.

Any mismatch => SOURCE_PROVENANCE_FAILURE.

## Controls

The existing three V0.1.4 control values remain mandatory in addition to 601/601 overlap equivalence.

## Stage-A release

Only a 608/608 exact daily ledger with:
- 3/3 controls exact;
- 601/601 legacy overlap exact;
- 7/7 missing dates newly materialized;
- deterministic lifecycle dataset hashes;
- deterministic final daily-series hash;

may emit SOURCE_REPLICATION_PASS.

Stage B remains physically and scientifically closed until that classification exists.

No market prices, returns, signal evaluation, PnL, or post-outcome tuning are authorized by this addendum.
