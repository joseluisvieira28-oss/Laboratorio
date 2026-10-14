# LVAC-TF-002 — FRESH DISCOVERY ECONOMIC CEILING RESULT V0.1

Date: 2026-09-26
Workflow run: 36229269997
Status: LVAC_TF_002_MEXC_ECONOMIC_CEILING_FAIL

## Frozen fresh Discovery dates
- 2023-04-05
- 2023-07-05
- 2023-10-04
- 2024-01-03

Per date:
- first 250,000 L2 messages
- public historical trades overlapping the same slice
- 1-second anchors
- 2025 OOS untouched
- 2026 holdout untouched

## Source scale
2023-04-05:
- 250,000 L2 states
- 24,821 anchors
- 310,214 overlapping trades

2023-07-05:
- 250,000 L2 states
- 24,475 anchors
- 60,192 overlapping trades

2023-10-04:
- 250,000 L2 states
- 24,746 anchors
- 156,667 overlapping trades

2024-01-03:
- 250,000 L2 states
- 24,251 anchors
- 156,782 overlapping trades
- historical cts coverage: 100%

## Feature-only calibration thresholds
Calibration date: 2023-04-05.

Liquidity depletion:
- p90 = 0.6469946150
- p95 = 0.7683905103
- p99 = 0.9180013886

Absolute aggressive-flow imbalance:
1s window:
- p75 = 1.0
- p90 = 1.0
- p95 = 1.0

5s window:
- p75 = 0.9463068164
- p90 = 0.9966492597
- p95 = 1.0

The 1-second flow-imbalance distribution is heavily saturated at |1|. This limits its ability to distinguish flow intensity and is recorded as a feature-design limitation, not tuned away after outcomes.

## Result
No predeclared variant/horizon satisfied:
- pooled n >= 40;
- pooled mean MEXC perfect-maker net > 0;
- positive date-level mean MEXC perfect-maker net in >=3/4 dates.

Survivors: 0.

Best pooled result:
- W5000_D99_F95
- 60s
- n = 74
- positive date count = 0/4
- mean directional mid = +1.6815 bps
- mean optimistic maker/maker gross = +1.7129 bps
- mean MEXC maker/maker net = -10.2871 bps
- mean MEXC taker/taker net = -14.3500 bps
- p95 optimistic maker/maker gross = +7.9752 bps

Second best:
- W5000_D99_F90
- 60s
- n = 105
- mean maker/maker gross = +1.4002 bps
- MEXC maker/maker net = -10.5998 bps
- positive date count = 0/4

## Decision
LVAC-TF-002 is closed at the MEXC economic-ceiling stage.

Do not rescue by:
- changing percentile thresholds;
- cherry-picking dates;
- choosing only positive tail events after outcomes;
- opening 2025 OOS;
- opening 2026 holdout.

## Next distinct family
SWEEP-CONT-003:
aggressive notional burst + actual BBO displacement + failure of depleted-side liquidity to replenish, tested on fresh 2024 Discovery dates.

This changes the economic mechanism from static/relative state prediction to post-sweep continuation.
