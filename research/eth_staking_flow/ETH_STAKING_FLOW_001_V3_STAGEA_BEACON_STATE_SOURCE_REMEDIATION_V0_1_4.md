# ETH-STAKING-FLOW-001 — V3 STAGE-A INDEPENDENT BEACON-STATE SOURCE REMEDIATION V0.1.4

Date: 2026-09-19
Status: **FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

## Context

The canonical Stage-A source remains Xatu `canonical_beacon_validators`. Runs V0.1, V0.1.1, V0.1.2 and V0.1.3 established that exactly seven frozen dates cannot be materialized from the canonical public Parquet objects:

- 2025-02-25
- 2025-02-26
- 2025-02-27
- 2025-02-28
- 2025-03-01
- 2025-10-18
- 2025-10-19

V0.1.3 proved that for these dates the relevant Parquet row groups contain zero usable `epoch_start_date_time` rows. This is a source-coverage defect, not a market result.

No signal, ETH price, return, PnL, or replication outcome has been opened.

## Narrow remediation

This amendment permits a second, protocol-native source only for the exact seven missing dates: the standard Ethereum Beacon API endpoint

`GET /eth/v1/beacon/states/{state_id}/validators?status=pending_queued&status=active_exiting`.

The semantic target is unchanged:
- first canonical epoch at or after 00:00:00 UTC;
- bounded within +32 slots;
- exact counts of `pending_queued` and `active_exiting`;
- `net_queue_count = pending_queued - active_exiting`.

No other source date may be substituted.

## Frozen independent endpoints

Probe all of:
1. `https://beaconstate-mainnet.chainsafe.io`
2. `https://beaconstate.ethstaker.cc`
3. `http://testing.mainnet.beacon-api.nimbus.team`

These endpoints were selected before the first V0.1.4 network request from the community-maintained Ethereum mainnet checkpoint endpoint registry.

## Exact control-equivalence gate

Before any missing date is admitted, the Beacon API route must reproduce the already-canonical Xatu values exactly on all three controls:

### 2025-02-24
- selected epoch: 347738
- selected unix time: 1740355415
- pending_queued: 0
- active_exiting: 5
- net_queue: -5

### 2025-03-02
- selected epoch: 349088
- selected unix time: 1740873815
- pending_queued: 0
- active_exiting: 0
- net_queue: 0

### 2025-10-17
- selected epoch: 400613
- selected unix time: 1760659415
- pending_queued: 48
- active_exiting: 55209
- net_queue: -55161

For every control and missing date:
- at least two independent frozen endpoints must return usable results;
- all usable endpoints must agree exactly on the two status counts;
- the queried state slot must equal the first epoch boundary at/after 00:00 UTC derived from the same Ethereum genesis-time/384-second epoch geometry used by the canonical Xatu timestamps;
- any endpoint disagreement = `SOURCE_PROVENANCE_FAILURE`;
- fewer than two usable endpoints for any required date = `SOURCE_ACQUISITION_TECHNICAL_FAILURE`.

Only if all three controls match Xatu exactly may the seven missing dates be emitted as `BEACON_API_EQUIVALENT_SOURCE_RECOVERY_PASS`.

## Stage-A consequence

A source-remediation PASS does not itself grant `SOURCE_REPLICATION_PASS`.
It authorizes replacing only the seven Xatu-empty dates in the 608-day Stage-A source ledger, after which the unchanged aggregate must still prove:
- exactly 608/608 daily observations;
- identical signal semantics;
- deterministic source lineage;
- all original integrity gates.

Stage B market outcomes remain dormant until that aggregate emits `SOURCE_REPLICATION_PASS`.

## Hard firewall

No ETH/BTC prices.
No returns.
No signal evaluation.
No PnL.
No 2026 source after 2026-08-31.
No market date after 2026-09-08.
No live trading, orders, wallets, exchange mutation, alerts/webhooks, or main merge.
No change to threshold, 90-day lookback, direction, 7-day hold, costs, non-overlap, or V3 gates.
