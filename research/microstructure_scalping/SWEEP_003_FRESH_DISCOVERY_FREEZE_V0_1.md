# SWEEP-003 — AGGRESSIVE SWEEP / MULTI-LEVEL CONSUMPTION
## FRESH DISCOVERY ECONOMIC CEILING — PRE-RUN FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Phase: DISCOVERY ONLY

## Hypothesis
A short burst of one-sided aggressive trades that executes across multiple price levels and moves the BBO may mark a microstructure shock whose immediate aftermath has either:
A. continuation, or
B. reversal,
large enough to exceed the current MEXC fee hurdle.

This is distinct from static imbalance, liquidity depletion alone, and flow-imbalance-only rules.

## Fresh Discovery dates
Calendar rule frozen before outcomes:
first Wednesday of each of the next three calendar months after the last fresh date used by LVAC-TF-002.

- 2024-02-07
- 2024-03-06
- 2024-04-03

All are inside 2023–2024 Discovery.
2025 OOS = LOCKED.
2026 holdout = LOCKED.

## Source
For each date:
- Bybit BTCUSDT linear L2
- first 250,000 L2 messages
- public historical BTCUSDT trades overlapping the L2 slice
- 1-second anchors
- source event clock = cts when available, otherwise ts

## Causal sweep state
At each 1-second anchor t, use only trades with timestamp strictly < t.

Trailing windows:
- 500 ms
- 1,000 ms

For each window compute:
- buy_notional
- sell_notional
- signed_flow = (buy_notional-sell_notional)/(buy_notional+sell_notional)
- dominant_side_notional
- number of distinct executed prices on dominant taker side
- dominant-side price span in bps
- BBO mid displacement from previous one-second anchor

Sweep direction:
- LONG if signed_flow > 0
- SHORT if signed_flow < 0

A valid sweep requires the BBO mid displacement over the last anchor interval to agree with sweep direction.

## Feature-only calibration
Use 2024-02-07 only to derive causal feature thresholds, never outcomes.

Percentiles:
- dominant-side notional: p90 / p95 / p99
- dominant-side price-span bps: p75 / p90 / p95

Price-level count gates are fixed integers:
- >= 2
- >= 3
- >= 5 distinct executed prices

No outcome-based threshold search.

## Predeclared variants
For each trailing window (500ms, 1000ms):

1. N90 + SP75 + L2
2. N95 + SP75 + L3
3. N95 + SP90 + L3
4. N99 + SP90 + L3
5. N99 + SP95 + L5

where N = notional percentile, SP = dominant-side price-span percentile, L = minimum distinct executed price levels.

For every event test BOTH predeclared post-shock hypotheses:
- CONTINUATION: trade in sweep direction
- REVERSAL: trade opposite sweep direction

Cooldown:
- 10 seconds after a selected event within each variant.

## Horizons
- 5s
- 15s
- 30s
- 60s
- 120s

## Economic ceiling
Report executable taker/taker and impossible perfect maker/maker upper bound.

MEXC API fee hurdles:
- taker/taker: 16 bps
- maker/maker: 12 bps

No slippage, latency, queue penalty or adverse selection in the perfect-maker ceiling.

## Survival rule
A variant × post-shock hypothesis × horizon is a CEILING_SURVIVOR only when:
- pooled n >= 30
- pooled mean MEXC perfect-maker net > 0
- at least 2 of 3 date-level means > 0

This is a feasibility ceiling only.
No candidate may enter OOS directly from this run.
