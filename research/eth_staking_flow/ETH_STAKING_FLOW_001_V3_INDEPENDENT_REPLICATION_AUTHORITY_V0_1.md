# ETH-STAKING-FLOW-001 — V3 INDEPENDENT REPLICATION AUTHORITY V0.1

Date: 2026-09-18
Policy: ND-PROMOTION-POLICY-V3.0-FROZEN
Branch: `eth-staking-flow-v0.3-discovery`
Status: **FROZEN BEFORE ANY 2025/2026 SOURCE OR MARKET ACCESS UNDER THIS REPLICATION**

## Historical Discovery preserved

Exact MVE: `ESF-NETQUEUE-XATU-7D-003`.

One-shot Discovery run:
- run: `35387086232`
- artifact: `ETH_STAKING_FLOW_001_DISCOVERY_V0_1`
- artifact id: `10564142616`
- artifact ZIP digest: `sha256:fcfb9b547cdd9716fe7043b98209bf39fe95875850db25ddbbfa1f62dc0efa98`
- historical classification: **DISCOVERY_INSUFFICIENT_SAMPLE**
- resolved non-overlapping events: **19**
- mean NET10: **+0.025716111971649736**
- PF NET10: **2.038225339621277**
- stationary-bootstrap one-sided p(mean NET10 <= 0): **0.0988901109889011**

The frozen Discovery minimum was 30 events. That failure is immutable. V3 does not rewrite it and this replication is not permission to reduce that minimum.

## Why a new replication is legitimate

Promotion Policy V3 treats `INSUFFICIENT_SAMPLE` as unresolved/non-scientific rather than Tier 4 and permits rare/event-driven mechanisms to accumulate disjoint independent historical blocks without arbitrary forward-event waiting, provided rules remain unchanged and the independent blocks were untouched before their prospective authority.

The 2025 and 2026 market/source blocks below were not opened by the V0.3 Discovery. They are therefore prospectively frozen now as two separate independent replication blocks.

## Exact unchanged mechanism

No scientific rule changes from the Discovery contract:

- predictor: `net_queue_count = pending_queued_count - active_exiting_count`;
- threshold: current value >= linear 80th percentile of exactly 90 PRIOR daily observations;
- current day excluded from threshold window;
- direction: LONG ETH only;
- instrument: Binance Spot ETHUSDT;
- entry: next UTC daily open after signal date;
- exit: UTC daily open 7 calendar days after entry;
- signal-to-exit geometry: signal t -> entry t+1 -> exit t+8;
- non-overlap: after accepting signal t, next eligible signal date = t+8;
- BASE round-trip cost: 10 bps;
- STRESS round-trip cost: 20 bps;
- no stop, target, leverage, short leg, BTC filter, funding filter, volatility filter, percentile change, lookback change or horizon change.

## Independent replication blocks

### Block R1 — 2025
Signal-date evaluation window:
`2025-01-01..2025-12-23`.

Price exit ceiling:
`2025-12-31`.

Source queue reconstruction required:
`2025-01-01..2025-12-31`, with prior-90 queue lookback supplied only by the already-canonical 2024 queue source where needed.

### Block R2 — 2026 protected historical-to-date
Signal-date evaluation window:
`2026-01-01..2026-08-31`.

Price exit ceiling:
`2026-09-08`.

Source queue reconstruction required:
`2025-10-03..2026-08-31` for the prior-90 context and signal dates. For canonical simplicity the source gate may reconstruct the full contiguous `2025-01-01..2026-08-31` range once and partition it afterward.

No source date after **2026-08-31** and no market date after **2026-09-08** is authorized by this authority.

The September 2026 source/signal block remains unopened.

## Stage A — source-only gate, authorized now

Canonical source remains public ethPandaOps Xatu Parquet:
`canonical_beacon_validators/YYYY/M/D/0.parquet`.

Exact snapshot/count algorithm must be byte/semantic equivalent to V0.3D:
- first canonical epoch at/after 00:00 UTC;
- <= +32 slots;
- unique validator index;
- exact `pending_queued` and `active_exiting` counts;
- one daily aggregate only.

Stage A may open 2025 and 2026 Xatu source data only within the frozen range. It may NOT access ETH/BTC prices, returns, event outcomes, PnL or performance statistics.

SOURCE_REPLICATION_PASS requires:
- exactly 608 unique daily queue observations for 2025-01-01..2026-08-31 inclusive;
- 608/608 exact hour-0 objects;
- zero missing/duplicate/outside dates;
- all per-date integrity rules pass;
- deterministic daily-series SHA-256;
- no market outcomes opened.

Any failure stops before Stage B.

## Stage B — independent outcome replication, dormant until Stage A PASS

Only after Stage A PASS, a separate workflow may open official Binance Data Vision Spot ETHUSDT daily opens for:
- 2025-01 through 2025-12;
- 2026-01 through 2026-09 only as required to resolve exits through 2026-09-08.

It must preserve provider CHECKSUM verification.

R1 and R2 are evaluated separately using the unchanged signal.

## V3 replicated-corpus adjudication frozen before new outcomes

The historical Discovery corpus is block D.
Independent blocks are R1=2025 and R2=2026-01-01..2026-08-31.

A V3 Rare-Event Replicated Corpus PASS requires ALL:

1. pooled resolved event count across D+R1+R2 >= 30;
2. exactly 3 disjoint blocks are represented;
3. R1 and R2 are genuinely independent from the original Discovery;
4. D, R1 and R2 each have mean NET10 > 0 and PF NET10 > 1;
5. pooled mean NET10 > 0 and pooled PF NET10 > 1;
6. every leave-one-block-out pooled result has mean NET10 > 0 and PF NET10 > 1;
7. largest known single positive event <= 40% of pooled positive NET10;
8. unchanged signal/direction/horizon/cost/event inclusion is verified;
9. clean source/provenance/leakage;
10. no adequate independent block materially contradicts base economics.

If any condition fails, **NO V3 TIER-2 PROMOTION**.

The original Discovery classification remains `DISCOVERY_INSUFFICIENT_SAMPLE` regardless of this later adjudication.

## Statistical reporting

For each independent block and pooled corpus report:
- N;
- mean/median NET10;
- PF NET10;
- mean/PF NET20;
- win rate;
- stationary-bootstrap p-value using the unchanged Discovery bootstrap settings when N > 0;
- concentration of largest positive event.

Replication block positivity/PF and the V3 corpus rules above control the V3 adjudication. No new threshold or p-value may be invented after outcomes.

## Safety

Research-only / fail-closed.
No live trading.
No authenticated exchange account/API.
No orders.
No wallets.
No exchange mutation.
No alerts/webhooks.
No main merge.
No post-outcome tuning.
No source or market access beyond the explicit frozen cutoffs above.
