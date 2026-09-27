# MICROSTRUCTURE SCALPING LAB V0.1 — PRE-OUTCOME FREEZE

Date: 2026-09-25
Status: SOURCE/DATA FEASIBILITY ONLY
Branch: microstructure-scalping-lab-v0.1

## Objective
Test whether observable crypto microstructure states contain short-horizon predictive information that remains economically positive after realistic fees, spread, slippage and latency.

This is a new economic hypothesis. It MUST NOT rescue, retune or reinterpret failed Scalping V1–V5.1, AggTrades V2, or prior HH:00 microstructure work.

## Governance
- Research only.
- No live trading, exchange mutation, wallets or capital.
- No merge to main without explicit operator authorization.
- Fail closed on timestamp ambiguity, missing sequence integrity, look-ahead, unavailable historical L2, or unverifiable cost assumptions.
- 2026/protected holdout remains unopened unless separately authorized by existing governance.
- No post-outcome threshold tuning.
- Source/Data Gate precedes Discovery.

## Primary hypothesis
At time t, pre-existing order-book/trade-flow state predicts executable future mid-price movement over ultra-short horizons strongly enough to exceed total implementation cost.

## Candidate observable features
Only features reconstructible strictly from information available by t:
- bid/ask spread
- top-of-book and depth imbalance (L1/L5/L10 where source permits)
- microprice displacement
- signed aggressive trade imbalance
- trade intensity / inter-arrival time
- depth additions/removals and cancellation asymmetry, only if event-level source permits defensible reconstruction
- short-horizon realized volatility
- liquidity pull / refill
- cross-market leader/follower state, only with timestamp-compatible sources

## Frozen label horizons
Evaluate future mid-price returns at:
100 ms, 500 ms, 1 s, 5 s, 15 s, 30 s.
A horizon unsupported by source timestamp resolution is BLOCKED, not approximated.

## Economic test
All candidate results must be reported gross and net of:
fees + half/full spread as applicable + slippage + latency sensitivity.
No edge may be promoted from gross returns alone.

## Required gates
1. SOURCE_AUTHORITY
2. TIMESTAMP_AND_SEQUENCE_INTEGRITY
3. RECONSTRUCTION_VALIDITY
4. COST_MODEL
5. DISCOVERY
6. OOS
7. LOCKED_HOLDOUT when governance permits
8. FORWARD_SHADOW

Allowed terminal states:
- SURVIVES
- NO_EDGE
- BLOCKED

## First attack
Perform a data-first source audit for historical event-level trades and L2/depth data. Record:
venue, instrument, period, granularity, timestamps, sequence IDs, depth semantics, public/free accessibility, rate/archive limitations, and whether deterministic replay is possible.

Do not run outcome tests until the Source/Data Gate is frozen.
