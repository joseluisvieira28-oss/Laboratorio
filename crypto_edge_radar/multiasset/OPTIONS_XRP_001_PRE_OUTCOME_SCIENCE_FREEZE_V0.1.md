# OPTIONS-XRP-001 — PRE-OUTCOME SCIENCE FREEZE V0.1

Status: FROZEN BEFORE XRP OUTCOME ACCESS
Date: 2026-10-02
Mode: research-only / fail-closed

## Hypothesis
A same-day XRP option trade-implied call-minus-put IV skew contains directional information for the next XRP daily open-to-open return.

## Frozen mechanism
- asset: XRP
- native options source family: Deribit XRP linear USDC options
- execution/outcome asset: XRP
- DTE: 7..120 calendar days
- call moneyness strike/index: 1.05..1.20
- put moneyness strike/index: 0.80..0.95
- minimum distinct eligible instruments per side/day: 3
- per-instrument aggregation: median trade IV
- daily skew: median(call instrument IV) - median(put instrument IV)
- position: +1 if skew > 0; -1 if skew < 0; 0 if skew = 0
- outcome: XRP daily open at t+1 to XRP daily open at t+2, aligned to position
- no regime filter
- no sign inversion
- no threshold optimization
- base execution-cost hurdle: 10 bps round trip
- stress diagnostic: 20 bps round trip
- HAC regression lags: 7

The DTE/min-side differences versus BTC are frozen before outcomes because current XRP options listing policy is structurally shorter/sparser.

## Development window
Maximum defensible contiguous historical window ending 2024-12-31 after Source/Data Gate. Exact start source-determined and recorded before outcomes.

## Protected OOS
2025 locked until Development classification and separate OOS authority. 2026 locked.

## Discovery gates
Candidate requires all:
- n >= 150 entered days;
- beta > 0 and one-sided HAC p <= 0.10;
- net mean after 10 bps > 0;
- PF after 10 bps > 1.0;
- at least 2 source-complete calendar years with >=25 entered days and nonnegative 10 bps net mean;
- no single year >75% of positive gross PnL;
- provenance/leakage PASS.

If source history is too short, classify INSUFFICIENT_HISTORY_FOR_PROMOTION rather than weakening gates.

No live authority is created.
