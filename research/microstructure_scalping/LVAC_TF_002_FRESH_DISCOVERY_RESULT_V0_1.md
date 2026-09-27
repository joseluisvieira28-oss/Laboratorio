# LVAC-TF-002 — FRESH DISCOVERY ECONOMIC CEILING RESULT

Date: 2026-09-26
Workflow run: 36229269997
Status: LVAC_TF_002_MEXC_ECONOMIC_CEILING_FAIL

## Fresh Discovery dates
- 2023-04-05
- 2023-07-05
- 2023-10-04
- 2024-01-03

All are inside the frozen 2023–2024 Discovery partition.
2025 OOS remained locked.
2026 protected holdout remained locked.

## Source coverage
Each date used the first 250,000 Bybit BTCUSDT L2 messages plus overlapping public historical trades.

Observed overlap-trade counts:
- 2023-04-05: 310,214
- 2023-07-05: 60,192
- 2023-10-04: 156,667
- 2024-01-03: 156,782

Historical cts coverage was 0% for the three 2023 samples and 100% for 2024-01-03.

## Feature-only calibration
Depletion thresholds from 2023-04-05:
- p90: 0.6469946150
- p95: 0.7683905103
- p99: 0.9180013886

Flow magnitude thresholds:
1s:
- p75 = 1
- p90 = 1
- p95 = 1

5s:
- p75 = 0.9463068164
- p90 = 0.9966492597
- p95 = 1

The 1s flow-imbalance feature saturates at |1| across the upper quartile and therefore has weak ranking resolution in this construction.

## Result
No predeclared variant/horizon satisfied the family survival rule.

Best pooled economic-ceiling result:
- variant: W5000_D99_F95
- horizon: 60s
- n: 74
- positive date means: 0 / 4
- mean directional mid: +1.6815 bps
- mean optimistic maker-maker gross: +1.7129 bps
- mean MEXC perfect-maker net: -10.2871 bps
- p95 optimistic maker gross: +7.9752 bps

Second-best:
- W5000_D99_F90 / 60s
- n: 105
- mean perfect-maker gross: +1.4002 bps
- MEXC net: -10.5998 bps
- positive dates: 0 / 4

## Decision
LVAC-TF-002 = ECONOMIC_CEILING_FAIL.

Do not tune the depletion or flow thresholds from these outcomes.
Do not open 2025 OOS.
Do not open 2026 holdout.

Next family must target a different mechanism with inherently larger conditional moves.
