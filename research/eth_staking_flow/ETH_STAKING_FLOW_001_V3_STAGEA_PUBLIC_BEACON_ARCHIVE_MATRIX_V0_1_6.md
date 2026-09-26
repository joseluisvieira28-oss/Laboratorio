# ETH-STAKING-FLOW-001 — V3 STAGE-A PUBLIC BEACON ARCHIVE MATRIX V0.1.6

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND
Parent: V3 Stage-A SOURCE_ACQUISITION_TECHNICAL_FAILURE

## Purpose

Test a new set of public Ethereum Beacon API transports for exact historical validator-state recovery at the seven frozen missing dates.

This does not change the scientific source semantics.

## Frozen endpoints

Probe all of:

1. beaconcha.in checkpoint:
   https://sync-mainnet.beaconcha.in

2. PietjePuk checkpoint:
   https://checkpointz.pietjepuk.net

3. beaconstate.info:
   https://beaconstate.info

4. Lodestar ChainSafe:
   https://lodestar-mainnet.chainsafe.io

5. Alchemy public documentation demo:
   https://eth-mainnetbeacon.g.alchemy.com/v2/docs-demo

No endpoint may be added after the first V0.1.6 network request.

## Exact query

For target epoch E:
target slot S = E * 32.

Query each endpoint with the standard Beacon API:

GET /eth/v1/beacon/states/{S}/validators?status=pending_queued

GET /eth/v1/beacon/states/{S}/validators?status=active_exiting

Count the returned validator records exactly.

No current-state substitution.
No nearest slot.
No alternate state time.
No backward/forward fill.

## Frozen controls

All three controls remain exact:

2025-02-24:
- epoch 347738
- slot 11127616
- pending_queued 0
- active_exiting 5
- net_queue -5

2025-03-02:
- epoch 349088
- slot 11170816
- pending_queued 0
- active_exiting 0
- net_queue 0

2025-10-17:
- epoch 400613
- slot 12819616
- pending_queued 48
- active_exiting 55209
- net_queue -55161

An endpoint is CONTROL_PASS only if all six control status calls return HTTP 200 and all three date counts match exactly.

## Frozen missing dates

Only if an endpoint CONTROL_PASSes may it query:

- 2025-02-25 — epoch 347963 — slot 11134816
- 2025-02-26 — epoch 348188 — slot 11142016
- 2025-02-27 — epoch 348413 — slot 11149216
- 2025-02-28 — epoch 348638 — slot 11156416
- 2025-03-01 — epoch 348863 — slot 11163616
- 2025-10-18 — epoch 400838 — slot 12826816
- 2025-10-19 — epoch 401063 — slot 12834016

## Quorum and provenance

For every required missing date:
- at least TWO distinct frozen endpoints must be usable;
- all usable CONTROL_PASS endpoints must agree exactly on pending_queued and active_exiting counts.

If usable endpoints disagree:
SOURCE_PROVENANCE_FAILURE.

If fewer than two CONTROL_PASS endpoints can materialize every missing date:
SOURCE_ACQUISITION_TECHNICAL_FAILURE.

Only exact 2+ endpoint agreement on all seven dates may emit:
BEACON_ARCHIVE_RECOVERY_PASS.

## Stage-A consequence

A recovery PASS permits replacing only the seven missing source dates in the immutable 601-date V3 Stage-A corpus.

The final aggregate must still prove:
- 608/608 unique dates;
- exact frozen range through 2026-08-31;
- unchanged queue semantics;
- deterministic source lineage;
- no market outcomes.

Only final SOURCE_REPLICATION_PASS may release Stage B.

## Firewall

No ETH/BTC prices.
No returns.
No signal evaluation.
No PnL.
No source date after 2026-08-31.
No market data.
No live trading/orders/wallets/exchange mutation.
No main merge.
No tuning or rescue of signal rules.
