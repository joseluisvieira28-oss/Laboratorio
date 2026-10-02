# OPTIONS-ETH-001 — PRE-OUTCOME SCIENCE FREEZE V0.1

Status: FROZEN BEFORE ETH OUTCOME ACCESS
Date: 2026-10-02
Mode: research-only / fail-closed

## Hypothesis
A same-day ETH option trade-implied call-minus-put IV skew contains directional information for the next ETH daily open-to-open return.

## Frozen mechanism
- asset: ETH
- native options source family: Deribit ETH options
- execution/outcome asset: ETH
- DTE: 30..120 calendar days
- call moneyness strike/index: 1.05..1.20
- put moneyness strike/index: 0.80..0.95
- minimum distinct eligible instruments per side/day: 5
- per-instrument aggregation: median trade IV
- daily skew: median(call instrument IV) - median(put instrument IV)
- position: +1 if skew > 0; -1 if skew < 0; 0 if skew = 0
- outcome: ETH daily open at t+1 to ETH daily open at t+2, aligned to position
- no regime filter in initial parent test
- no sign inversion
- no threshold optimization
- base execution-cost hurdle: 10 bps round trip
- stress diagnostic: 20 bps round trip
- HAC regression lags: 7

## Development window
Use the maximum defensible contiguous historical window ending 2024-12-31 after Source/Data Gate. The exact start date is determined only by source availability and must be recorded before outcomes.

## Protected OOS
2025 is locked until Development classification and a separate OOS authority. 2026 is locked.

## Discovery gates
Candidate requires all:
- n >= 250 entered days;
- beta > 0 and one-sided HAC p <= 0.10;
- net mean after 10 bps > 0;
- PF after 10 bps > 1.0;
- at least 2 calendar years with >=40 entered days and nonnegative 10 bps net mean;
- no single year >70% of total positive gross PnL;
- all provenance/leakage gates PASS.

Otherwise classify NO_DISCOVERY_EDGE or INSUFFICIENT_SAMPLE. Source failure is SOURCE_BLOCKED, never NO_EDGE.

No live authority is created by this freeze.
