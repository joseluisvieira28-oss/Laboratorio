# ETH-STAKING-FLOW-001 — PRE-DISCOVERY AUTHORITY V0.1

Status: FROZEN PRE-OUTCOME / SOURCE-DATA GATE ONLY
Frozen UTC date: 2026-09-14
Repository: joseluisvieira28-oss/Laboratorio
Branch: eth-staking-flow-v0.1

## Governance
Research-only. Fail-closed. No live trading, exchange mutation, orders, deployment, merge to main, post-outcome tuning, or rescue of historical hypotheses.
This authority does not authorize Discovery or access to ETH/BTC price values.
2025_ACCESS_ALLOWED=false
2026_ACCESS_ALLOWED=false
PRICE_VALUES_ALLOWED=false
RETURNS_ALLOWED=false
PNL_ALLOWED=false

## Anti-duplication
Canonical searches required across Google Drive, ChatGPT File Library, GitHub branches/code/commits/artifacts/manifests/closeouts, and Crypto project history.
Closest canonical record: CRYPTO LABS — GAP ANALYSIS V2 — NEW MECHANISM FRONTIER — 2026-09-14, where #10 is QUEUED and conditioned on reproducible daily historical queue snapshots.
No completed or active canonical ETH staking-queue/validator-flow laboratory was found at freeze time.
Overlap classification: NONE for a completed canonical experiment; PLANNED_ONLY in the roadmap.

## Frozen MVE
MVE ID: ESF-NETQUEUE-7D-001
Family ID: ETH-STAKING-FLOW-001

Economic hypothesis:
A large positive net validator entry-queue pressure state represents stronger marginal demand to lock ETH than demand to exit. It is expected to precede a positive future ETH return.

Single source variable:
net_queue_count_t = pending_queued_count_t - active_exiting_count_t

Observation timestamp:
One observation per UTC day at the first canonical consensus state at or after 00:00:00 UTC. If the exact target slot is skipped/unavailable, select the first canonical state within the next 32 slots and record the selected slot and offset. No backward fill, interpolation, current-state substitution, or later-revised queue reconstruction.

Source window:
2023-04-12 through 2024-12-31 inclusive. Source-only access.
Historical source must expose consensus state keyed by historical slot/state root and validator status through the standard Beacon API:
GET /eth/v1/beacon/states/{state_id}/validators?status=pending_queued
GET /eth/v1/beacon/states/{state_id}/validators?status=active_exiting

Frozen signal for later separately-authorized Discovery:
At date t, after at least 90 prior daily observations, signal if net_queue_count_t is at or above the trailing 90-observation 80th percentile, computed using only observations available by t.
Direction: LONG ETH.
Execution: next UTC daily open after t.
Holding period: 7 calendar days.
Overlapping signals: blocked until the prior 7-day position closes.
Round-trip base cost: 10 bps.
Stress cost: 20 bps.
No stop, take-profit, leverage, short leg, BTC alternative, or secondary filter.

Frozen promotion gates for later Discovery:
- complete provenance and no leakage;
- at least 30 non-overlapping events;
- mean NET10 > 0;
- profit factor NET10 > 1.0;
- one-sided stationary-bootstrap p(mean NET10 <= 0) <= 0.10;
- both calendar blocks 2023 and 2024 non-negative when they contain at least 5 events;
- NET20 reported as fragility diagnostic and not used to rescue a base failure.
Any gate failure means no promotion under this MVE. No threshold, horizon, asset, cost, or sign change after outcomes.

## Source/Data gate
The source gate is outcome-blind and may only:
- test historical endpoint availability and authentication;
- acquire and hash source responses;
- enumerate coverage, missing target days, chosen slots, duplicate timestamps, response schemas and timestamp alignment;
- verify point-in-time semantics;
- create manifests and closeout;
- confirm market prices, returns and PnL were not accessed.

Valid terminal classifications:
SOURCE_DATA_PASS
SOURCE_AUTH_BLOCKED
SOURCE_ACQUISITION_TECHNICAL_FAILURE
DATA_FAILURE
PROVENANCE_FAILURE
INSUFFICIENT_SAMPLE

Never classify NO_EDGE at this phase.
