# OPTIONS-SOL-001 — PRE-OUTCOME SCIENCE FREEZE V0.1

Status: FROZEN BEFORE SOL OUTCOME ACCESS
Date: 2026-10-02
Mode: research-only / fail-closed

## Hypothesis
A same-day SOL option trade-implied call-minus-put IV skew contains directional information for the next SOL daily open-to-open return.

## Frozen mechanism
- asset: SOL
- native options source family: Deribit SOL linear USDC options
- execution/outcome asset: SOL
- DTE: 7..120 calendar days
- call moneyness strike/index: 1.05..1.20
- put moneyness strike/index: 0.80..0.95
- minimum distinct eligible instruments per side/day: 3
- per-instrument aggregation: median trade IV
- daily skew: median(call instrument IV) - median(put instrument IV)
- position: +1 if skew > 0; -1 if skew < 0; 0 if skew = 0
- outcome: SOL daily open at t+1 to SOL daily open at t+2, aligned to position
- no regime filter in initial parent test
- no sign inversion
- no threshold optimization
- base execution-cost hurdle: 10 bps round trip
- stress diagnostic: 20 bps round trip
- HAC regression lags: 7

The wider DTE floor and lower minimum-side count versus BTC are prospectively frozen before outcomes because current SOL listing policy is structurally shorter/sparser than BTC. They are not post-outcome adaptations.

## Development window
Use the maximum defensible contiguous historical window ending 2024-12-31 after Source/Data Gate. Exact start is source-determined and recorded before outcomes.

## Protected OOS
2025 locked until Development classification and separate OOS authority. 2026 locked.

## Discovery gates
Candidate requires all:
- n >= 150 entered days;
- beta > 0 and one-sided HAC p <= 0.10;
- net mean after 10 bps > 0;
- PF after 10 bps > 1.0;
- at least 2 calendar years with >=25 entered days and nonnegative 10 bps net mean, when two source-complete years exist;
- no single year >75% of total positive gross PnL;
- provenance/leakage PASS.

If fewer than two source-complete calendar years exist, multi-year stability cannot pass and the result is INSUFFICIENT_HISTORY_FOR_PROMOTION even if economics are positive.

No live authority is created.
