# SWEEP-CONT-003 — FRESH DISCOVERY ECONOMIC CEILING RESULT V0.1

Date: 2026-09-26
Workflow run: 36229620912
Status: SWEEP_CONT_003_MEXC_ECONOMIC_CEILING_FAIL

## Fresh Discovery dates
- 2024-03-06
- 2024-06-05
- 2024-09-04
- 2024-12-04

All four are inside frozen Discovery.
2025 OOS untouched.
2026 holdout untouched.

## Source scale
2024-03-06:
- 250,000 L2 states
- 24,029 anchors
- 699,493 overlapping trades
- cts coverage 100%

2024-06-05:
- 250,000 L2 states
- 23,983 anchors
- 259,611 overlapping trades
- cts coverage 100%

2024-09-04:
- 250,000 L2 states
- 23,932 anchors
- 787,039 overlapping trades
- cts coverage 100%

2024-12-04:
- 250,000 L2 states
- 23,800 anchors
- 296,659 overlapping trades
- cts coverage 100%

## Feature-only calibration thresholds
Calibration date: 2024-03-06.

Aggressive same-side 1s burst ratio vs preceding 60s:
- p95 = 14.7462339895x
- p99 = 43.5429847351x

One-second BBO displacement:
- p90 = 3.0019174551 bps
- p95 = 3.8145076911 bps

Top-10 swept-side replenishment failure:
- p75 = 0.5428745804

## Result
Survivors: 0.

Best pooled combination:
- C_B95_X95
- horizon 60s
- n = 217
- positive date count = 0/4
- mean future directional mid = +3.0844 bps
- mean perfect maker/maker gross = +3.1134 bps
- mean MEXC maker/maker net after fee only = -8.8866 bps
- mean MEXC taker/taker net = -12.9447 bps
- p95 perfect maker/maker gross = +23.7001 bps

Other variants were materially worse in mean economics.

## Decision
The frozen post-sweep continuation family does not clear current MEXC API fee economics, even under an impossible perfect maker/maker execution ceiling.

Do not rescue by:
- lowering burst/displacement thresholds after outcomes;
- selecting only the p95 tail winners;
- changing dates;
- opening OOS;
- opening the 2026 holdout.

## Implication
Single-venue microstructure signals tested so far are producing mean future displacement in low-single-digit bps, while current MEXC API round-trip fee hurdles are 12 bps maker/maker and 16 bps taker/taker.

Next distinct research direction:
XVENUE-LAG-004 — forward-only cross-venue price discovery / lag measurement using public market data on Binance, Bybit and MEXC from one collector clock.

This changes the mechanism from same-venue state prediction to external price-discovery transmission.
