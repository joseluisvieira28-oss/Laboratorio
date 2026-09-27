# XVENUE-LAG-005 — BINANCE→MEXC FORWARD LEAD-LAG
## SOURCE/SCHEMA GATE FREEZE V0.1

Date: 2026-09-26
Status: SOURCE/SCHEMA GATE ONLY

## Hypothesis
A public BBO move on a leader venue may arrive before the corresponding MEXC Futures BBO adjustment, creating a measurable forward lead-lag state.

This is distinct from:
- same-venue BTC microstructure prediction;
- BTC→ALT same-venue lead-lag;
- hourly H180-0001 lead-lag.

## First target
BTC perpetual:
- leader source: Binance USD-M BTCUSDT bookTicker
- follower/execution-observer source: MEXC BTC_USDT incremental depth + REST snapshot

## Source gate
Capture both streams in the SAME GitHub runner and record:
- local receive timestamp from monotonic/Unix clock
- exchange timestamp where supplied
- message schema
- best bid/ask fields or enough information to reconstruct them
- MEXC version continuity

No edge test until both stream schemas are proven.

No authentication.
No orders.
No exchange mutation.
