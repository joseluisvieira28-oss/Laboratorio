# XVENUE-LAG-004 — CROSS-VENUE PRICE-DISCOVERY LAG
## FORWARD PUBLIC-MARKET-DATA MVE — PRE-RUN FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Phase: FORWARD RESEARCH ONLY

## Hypothesis
A rapid BTCUSDT price move first observed on a high-liquidity leader venue may leave a short executable lag before the same move is fully reflected in MEXC BTC_USDT.

This is economically distinct from all prior single-venue microstructure families.

## Venues
Leader candidates:
- Binance USD-M BTCUSDT perpetual
- Bybit linear BTCUSDT perpetual

Execution/reference lag venue:
- MEXC BTC_USDT perpetual

Public market data only.
No authentication.
No orders.
No exchange mutation.

## Clock
Primary cross-venue clock:
collector monotonic receive timestamp on ONE GitHub Actions runner.

Exchange timestamps are preserved only as diagnostics.
They are NOT used to align venues because exchange clocks and publication paths differ.

## Forward sample
Total capture: 180 seconds.

Split by collector receive time:
- first 60 seconds = feature-only calibration;
- final 120 seconds = frozen evaluation.

No evaluation outcome can change calibration thresholds.

## Quote sampling
Construct a 50 ms receive-time grid using latest-known valid BBO from each venue.
An observation is valid only after all three venues have supplied a quote.

## Leader features
For Binance and Bybit independently:
leader mid return over:
- 100 ms
- 250 ms

Feature-only calibration thresholds:
absolute leader return p95 and p99 for each leader/window pair.

## Lag condition
At evaluation time t:
- leader absolute return >= frozen threshold;
- direction = sign(leader return);
- MEXC return over the same backward-looking window has same direction OR smaller magnitude;
- require abs(MEXC backward return) <= 50% of abs(leader backward return).

This identifies an observable leader move not yet fully reflected in MEXC.

Cooldown:
500 ms per leader/window/threshold variant.

## Future MEXC horizons
- 100 ms
- 250 ms
- 500 ms
- 1000 ms

## MEXC execution economics
From MEXC API Futures fees effective 2026-06-01:
- maker 6 bps per side;
- taker 8 bps per side.

Report:
- directional MEXC future mid return;
- taker/taker executable BBO gross and net after 16 bps fees;
- impossible perfect maker/maker BBO ceiling and net after 12 bps fees.

No slippage/adverse selection in the ceiling.

## Initial MVE interpretation
This 3-minute forward sample cannot promote an edge.

A variant is a FORWARD_CEILING_SIGNAL only if:
- evaluation n >= 20;
- mean perfect maker/maker MEXC net > 0.

Otherwise:
NO_FORWARD_CEILING_SIGNAL_SAMPLE.

Any signal still requires a long forward observation before OOS-style judgment or capital use.
