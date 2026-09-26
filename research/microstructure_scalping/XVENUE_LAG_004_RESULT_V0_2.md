# XVENUE-LAG-004 — FORWARD PUBLIC-MARKET-DATA MVE RESULT V0.2

Date: 2026-09-26
Workflow run: 36230315929
Status: NO_FORWARD_CEILING_SIGNAL_SAMPLE
Technical revision: V0.2_MEXC_DEPTH_STEP_BBO

## Scope
- Public market data only
- Binance USD-M BTCUSDT BBO
- Bybit linear BTCUSDT L1
- MEXC BTC_USDT depth.step market-level BBO
- single collector receive clock
- total overlap: 178.716 seconds
- first 60 seconds feature-only calibration
- final ~118.7 seconds evaluation
- no authentication
- no orders
- no exchange mutation

## Raw capture
- Binance quotes: 59,645
- Bybit quotes: 3,098
- MEXC quotes: 600
- aligned 50ms grid points: 3,573
- MEXC non-monotonic versions: 0
- MEXC version skips: 586 (diagnostic only; no incremental book reconstruction)
- collector errors: none

## Feature-only calibration thresholds
Binance:
- 100ms p95: 0.0000 bps
- 100ms p99: 0.6881 bps
- 250ms p95: 0.4034 bps
- 250ms p99: 0.9254 bps

Bybit:
- 100ms p95: 0.0949 bps
- 100ms p99: 1.0678 bps
- 250ms p95: 0.4629 bps
- 250ms p99: 1.3169 bps

## Result
Survivors: 0.

Best observed ceiling:
- leader: Bybit
- leader window: 250ms
- threshold: p99 = 1.3169 bps
- future MEXC horizon: 500ms
- n: 3
- mean directional MEXC mid: +2.0156 bps
- mean MEXC taker gross: +0.9771 bps
- mean MEXC taker net: -15.0229 bps
- mean perfect maker/maker gross: +3.0544 bps
- mean MEXC maker/maker net: -8.9456 bps

Other best variants remained in the same low-single-digit-bps range.

## Decision
No forward ceiling signal in this sample.

This short MVE is not sufficient to prove absence of cross-venue lead/lag generally, but it is sufficient to show that the observed lag magnitude is nowhere near current MEXC API transaction-cost hurdles in this sample.

Do not tune thresholds from this sample.

## Program implication
Across static imbalance, liquidity vacuum, aggressive-flow confirmation, post-sweep continuation and cross-venue lag, average gross continuation remains low-single-digit bps.

Current MEXC API fees create a structural hurdle:
- 12 bps maker/maker round trip
- 16 bps taker/taker round trip

Next research should target event families whose natural move scale is tens of bps, not ordinary microstructure noise.

Next distinct family:
REACTIVE-SHOCK-SCALP-005 — scheduled CPI/NFP post-release microstructure continuation using official event times, historical L2 and public trades, without consensus data.
