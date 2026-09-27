# SWEEP-003 — FRESH DISCOVERY ECONOMIC CEILING RESULT

Date: 2026-09-26
Workflow run: 36229673058
Status: SWEEP_003_MEXC_ECONOMIC_CEILING_FAIL

## Fresh Discovery dates
- 2024-02-07
- 2024-03-06
- 2024-04-03

2025 OOS remained locked.
2026 protected holdout remained locked.

## Source coverage
Each date used first 250,000 Bybit BTCUSDT L2 messages plus overlapping public trades.

Trade overlap:
- 2024-02-07: 157,712
- 2024-03-06: 699,493
- 2024-04-03: 390,705

## Frozen calibration
500 ms dominant-side notional:
- p90: 43,082.35
- p95: 96,972.99
- p99: 413,472.15

1000 ms dominant-side notional:
- p90: 60,750.19
- p95: 136,696.80
- p99: 550,859.30

500 ms price-span:
- p75: 0 bps
- p90: 0.2562 bps
- p95: 0.6537 bps

1000 ms price-span:
- p75: 0 bps
- p90: 0.4640 bps
- p95: 0.8646 bps

## Result
No continuation or reversal variant/horizon survived.

Best pooled mean by MEXC perfect-maker ceiling:
- variant: W1000_N99_SP90_L3
- mode: REVERSAL
- horizon: 120s
- n: 1,142
- positive date means: 0 / 3
- mean directional mid: +0.5455 bps
- mean optimistic maker-maker gross: +0.5733 bps
- mean MEXC maker-maker net: -11.4267 bps
- p95 optimistic maker gross: +30.3048 bps

Large tail outcomes exist but are not identified with positive average economics by the frozen signal.

## Decision
SWEEP-003 = ECONOMIC_CEILING_FAIL.

Do not outcome-tune notional/span/level thresholds.
Do not open 2025 OOS.
Do not open 2026 holdout.

Next mechanism should seek a follower asset with larger conditional movement rather than attempting to extract sub-bps continuation from BTC itself.
