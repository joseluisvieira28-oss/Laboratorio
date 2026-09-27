# LVAC-001 — LIQUIDITY VACUUM SCALPING — ECONOMIC CEILING MVE RESULT

Date: 2026-09-25
Workflow run: 36194690135
Status: LVAC_001_MEXC_ECONOMIC_CEILING_FAIL_SAMPLE

## Source
- Bybit BTCUSDT L2
- 2023-01-18
- first 250,000 messages
- 24,447 one-second anchors
- OOS 2025 untouched
- protected 2026 untouched

## Frozen depletion thresholds
- p90: 0.4582489005
- p95: 0.6069142964
- p99: 0.8183890392

## Result
No predeclared variant × threshold × horizon with n>=50 achieved positive mean MEXC maker-maker net under the deliberately optimistic perfect-fill ceiling.

Best mean combination:
- variant: depletion + L10 imbalance confirmation
- depletion bucket: top 1%
- horizon: 15s
- n: 170
- mean directional mid: +1.4687 bps
- mean optimistic maker-maker gross: +1.7124 bps
- mean MEXC maker-maker net after fee only: -10.2876 bps
- mean MEXC taker net: -14.7750 bps

At 30s for the same top-1% confirmed family:
- n: 169
- mean directional mid: +1.3129 bps
- mean optimistic maker-maker gross: +1.5580 bps
- mean MEXC maker-maker net: -10.4420 bps
- p95 optimistic maker-maker gross: +14.3732 bps

## Interpretation
The average liquidity-vacuum trigger is economically dead at current MEXC API fees, even with impossible perfect maker fills.

However, the upper tail contains rare events whose gross move can exceed the 12 bps maker/maker fee hurdle. The present depletion trigger does NOT identify those events reliably enough; using future outcomes to cherry-pick them is forbidden.

## Decision
LVAC-001 as currently frozen = ECONOMIC_CEILING_FAIL_SAMPLE.

Do not tune depletion thresholds on this day.

Scientifically legitimate next family:
LVAC-TF-002 — liquidity depletion plus causal pre-event aggressive trade-flow confirmation, tested on fresh Discovery dates and frozen before outcomes.

No OOS opened.
No holdout opened.
No live trading authority.
