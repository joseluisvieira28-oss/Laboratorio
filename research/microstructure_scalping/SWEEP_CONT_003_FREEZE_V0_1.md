# SWEEP-CONT-003 — AGGRESSIVE SWEEP CONTINUATION
## FRESH DISCOVERY ECONOMIC CEILING — PRE-RUN FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Phase: DISCOVERY ONLY

## Hypothesis
A completed one-second aggressive sweep that:
1. has same-side taker notional far above its own trailing baseline;
2. has already displaced the executable BBO in the sweep direction; and
3. optionally leaves the swept side under-replenished,

may identify continuation events whose subsequent 5–60 second move is materially larger than static imbalance/LVAC signals.

This is a post-sweep continuation hypothesis, not a static-order-book prediction.

## Deterministic fresh Discovery dates
Chosen before outcomes by calendar rule: first Wednesday of each quarter-ending month in 2024.

- 2024-03-06
- 2024-06-05
- 2024-09-04
- 2024-12-04

All are in the frozen 2023–2024 Discovery partition.
2025 OOS remains LOCKED.
2026 holdout remains LOCKED.

## Source
Per date:
- Bybit BTCUSDT historical L2, first 250,000 messages;
- historical public BTCUSDT trades overlapping the same L2 slice;
- one-second anchors;
- L2 cts preferred; ts fallback explicitly counted.

## Causal sweep construction

At anchor t, use only trades with timestamp < t.

### Aggressive direction
Trailing 1-second buy/sell notional:
notional = size * price.

direction:
- LONG if buy_notional_1s > sell_notional_1s
- SHORT if sell_notional_1s > buy_notional_1s
- no event if equal

### Burst ratio
Compare same-direction notional in the trailing 1 second with the per-second same-direction notional from the preceding 60 seconds, excluding the current 1-second burst.

burst_ratio = current_same_side_1s / (previous_same_side_60s / 60)

Anchors without positive baseline are ineligible.

### BBO displacement
For LONG:
(current ask - previous 1s ask) / previous ask.

For SHORT:
(previous 1s bid - current bid) / previous bid.

Only positive displacement qualifies.

### Replenishment failure
For LONG:
depletion of top-10 ask depth versus previous 1-second anchor.

For SHORT:
depletion of top-10 bid depth versus previous 1-second anchor.

Cancellations and executions are not separated here; this is only a contemporaneous post-sweep state feature.

## Feature-only calibration
2024-03-06 derives thresholds without using future returns.

Generic percentile families:
- burst_ratio: p95 / p99
- displacement_bps: p90 / p95
- replenishment_failure: p75

The numeric thresholds are held fixed for all four dates.

## Predeclared variants
A. B95 + X90
B. B99 + X90
C. B95 + X95
D. B99 + X95
E. B95 + X90 + R75
F. B99 + X90 + R75

All require:
- positive BBO displacement;
- flow direction = sweep direction;
- 10-second cooldown after selection.

## Horizons
- 5s
- 15s
- 30s
- 60s

Returns start at the post-sweep anchor, so the already-observed one-second sweep is NOT counted as future profit.

## Economic ceiling
Report:
- directional future mid move;
- executable taker/taker return, fee hurdle 16 bps;
- impossible perfect maker/maker upper bound, fee hurdle 12 bps.

No slippage, queue penalty, missed fills or adverse selection are charged to the maker ceiling.

## Survival rule
A variant/horizon is a CEILING_SURVIVOR only if:
- pooled n >= 40;
- pooled mean MEXC perfect-maker net > 0;
- at least 3 of 4 dates have positive date-level mean MEXC perfect-maker net.

No outcome-based threshold rescue.
No OOS opening from a failed ceiling.
