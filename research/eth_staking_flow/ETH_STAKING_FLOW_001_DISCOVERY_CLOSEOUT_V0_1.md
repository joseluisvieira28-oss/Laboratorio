# ETH-STAKING-FLOW-001 / ESF-NETQUEUE-XATU-7D-003 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-18
Branch: `eth-staking-flow-v0.3-discovery`
Historical verdict: **DISCOVERY_INSUFFICIENT_SAMPLE**

## Canonical evidence

- Discovery run: `35387086232`
- workflow conclusion: SUCCESS
- artifact: `ETH_STAKING_FLOW_001_DISCOVERY_V0_1`
- artifact id: `10564142616`
- artifact ZIP SHA-256: `fcfb9b547cdd9716fe7043b98209bf39fe95875850db25ddbbfa1f62dc0efa98`
- frozen source run: `35384444641`
- frozen 630-day source series SHA-256: `95d225db9c4924852dfbca6333122fc78199092f0cdfd7a0995f4b5530cb2544`

## Frozen mechanism

Unchanged from the pre-Discovery freeze:

- source variable: pending_queued minus active_exiting validators;
- signal: current net queue count >= linear 80th percentile of exactly 90 PRIOR daily observations;
- LONG ETHUSDT Spot;
- next UTC daily open entry;
- 7-calendar-day hold;
- non-overlapping positions;
- 10 bps BASE / 20 bps STRESS round-trip cost;
- no stop, target, leverage, short leg, BTC filter, regime filter or threshold sweep.

## Canonical result

Resolved non-overlapping events: **19**.

Frozen minimum sample: **30**.

Therefore the exact historical Discovery verdict is and remains:

**DISCOVERY_INSUFFICIENT_SAMPLE**

Positive diagnostics preserved, but not promoted:

- mean NET10: **+0.025716111971649736** per resolved event;
- PF NET10: **2.038225339621277**;
- stationary-bootstrap one-sided p(mean NET10 <= 0): **0.0988901109889011**.

The statistical/economic diagnostics are interesting, but they do not override the prospectively frozen minimum sample rule.

## Scientific interpretation

This result is not `NO_EDGE`, not Tier 4 and not a promotion. Under Promotion Policy V3, `INSUFFICIENT_SAMPLE` remains an unresolved/non-scientific state.

No threshold, lookback, direction, horizon, cost, overlap rule, asset or event-selection rescue is authorized.

A separately prospectively frozen V3 independent-replication campaign may accumulate genuinely independent untouched blocks under the exact unchanged rules. Such later evidence cannot rewrite this historical Discovery classification.

## Safety receipt

- 2025 accessed by Discovery: false
- 2026 accessed by Discovery: false
- live trading: false
- orders: false
- wallets: false
- exchange mutation: false
- authenticated exchange API: false
- merge to main: false
