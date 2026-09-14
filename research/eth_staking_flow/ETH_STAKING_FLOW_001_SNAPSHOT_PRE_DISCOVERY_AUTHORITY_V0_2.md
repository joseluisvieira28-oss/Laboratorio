# ETH-STAKING-FLOW-001 — SNAPSHOT SOURCE REMEDIATION — PRE-DISCOVERY AUTHORITY V0.2

Status: FROZEN PRE-OUTCOME / SOURCE-DATA GATE ONLY
Frozen UTC date: 2026-09-14
Repository: joseluisvieira28-oss/Laboratorio
Branch: eth-staking-flow-v0.2

## Governance
Research-only. Fail-closed. No live trading, exchange mutation, orders, deployment, merge to main, post-outcome tuning, cherry-picking, or rescue of failed historical hypotheses.
This authority does not authorize Discovery or access to ETH/BTC market-price values.
2025_ACCESS_ALLOWED=false
2026_ACCESS_ALLOWED=false
PRICE_VALUES_ALLOWED=false
RETURNS_ALLOWED=false
PNL_ALLOWED=false

## Relationship to V0.1
ETH-STAKING-FLOW-001 / ESF-NETQUEUE-7D-001 remains SOURCE_AUTH_BLOCKED under its original frozen historical Beacon-state contract. It is not modified, reopened, or reclassified by this authority.

V0.2 is a new prospective MVE because it changes the source representation and source window before any outcome has been opened. The economic mechanism remains ETH validator entry-versus-exit queue pressure, but no V0.1 source rule is silently substituted.

## New frozen MVE
MVE ID: ESF-NETQUEUE-SNAPSHOT-7D-002
Family ID: ETH-STAKING-FLOW-001

Economic hypothesis:
A large positive validator net-entry queue-pressure state represents stronger marginal demand to lock ETH than demand to exit, and is expected to precede a positive future ETH return.

Single source variable:
net_queue_count_t = entry_queue_t - exit_queue_t

Source fields are validator counts, as defined by the pinned source implementation using beaconcha.in `beaconchain_entering` and `beaconchain_exiting`.

## Frozen source definition
Public source repository: etheralpha/validatorqueue-com
Pinned source commit: 4d6d9604a9aa4a126cedbc8c8cabff5295fffc8e
Pinned source file: historical_data.json
Pinned implementation file: build.py
Pinned workflow file: .github/workflows/update_validator_data.yml

Source window: 2023-05-21 through 2024-12-31 inclusive.
Expected daily rows if complete: 591.

Observation semantics:
One persisted observation per UTC calendar date. The pinned implementation appends at most one row for the current UTC date, and the pinned workflow is scheduled every 6 minutes. Therefore the observation is the first successfully persisted source snapshot for that UTC date, not an exact 00:00 consensus-state snapshot.

No backward fill, interpolation, current-state substitution, or access to post-2024 source rows is permitted.

## Point-in-time / provenance gate
The Source/Data Gate must fail closed unless all of the following are proven from the pinned public Git history through the pinned 2024-12-31 commit:
- exact calendar coverage 2023-05-21 through 2024-12-31;
- exactly 591 unique UTC dates;
- zero duplicate dates and zero missing dates;
- `entry_queue` and `exit_queue` present, integer-like, and non-negative for every row;
- every source date first appears in a Git commit on that same UTC calendar date;
- once a date first appears, its `entry_queue` and `exit_queue` values are append-only stable through the pinned commit;
- pinned `build.py` proves the queue fields are sourced from `beaconchain_entering` and `beaconchain_exiting`;
- pinned workflow proves scheduled acquisition and persistence of `historical_data.json`;
- raw pinned source bytes and provenance files are hashed and preserved.

If any condition fails, classify DATA_FAILURE or PROVENANCE_FAILURE as appropriate. Never classify NO_EDGE at this phase.

## Frozen signal for later separately-authorized Discovery
At date t, after at least 90 prior daily observations, signal if net_queue_count_t is at or above the trailing 90-observation 80th percentile, computed using only observations available by t.
Direction: LONG ETH.
Execution: next UTC daily open after t.
Holding period: 7 calendar days.
Overlapping signals: blocked until the prior 7-day position closes.
Round-trip base cost: 10 bps.
Stress cost: 20 bps.
No stop, take-profit, leverage, short leg, BTC alternative, secondary filter, threshold rescue, horizon rescue, or cost rescue.

## Frozen promotion gates for later Discovery
- complete provenance and no leakage;
- at least 30 non-overlapping events;
- mean NET10 > 0;
- profit factor NET10 > 1.0;
- one-sided stationary-bootstrap p(mean NET10 <= 0) <= 0.10;
- both calendar blocks 2023 and 2024 non-negative when they contain at least 5 events;
- NET20 reported only as a fragility diagnostic and never used to rescue a base failure.

Any gate failure means no promotion under this MVE. No threshold, horizon, asset, cost, sign, source window, or source representation change after outcomes.

## Source/Data Gate permissions
The source gate may only acquire/hash the pinned public source and Git history, verify coverage/schema/timestamps/append-only provenance, and create receipts/manifests/evidence artifacts.
It must not access ETH/BTC market prices, calculate the signal series, count later Discovery events, calculate returns/PnL, open 2025/2026, or evaluate economic performance.

Valid terminal classifications:
SOURCE_DATA_PASS
SOURCE_AUTH_BLOCKED
SOURCE_ACQUISITION_TECHNICAL_FAILURE
DATA_FAILURE
PROVENANCE_FAILURE
INSUFFICIENT_SAMPLE

Discovery remains separately authorization-gated even if SOURCE_DATA_PASS is reached.
