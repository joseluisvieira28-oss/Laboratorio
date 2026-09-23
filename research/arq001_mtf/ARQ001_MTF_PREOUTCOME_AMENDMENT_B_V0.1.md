# ARQ-001-MTF-001 — PRE-OUTCOME IMPLEMENTATION AMENDMENT B V0.1

Date: 2026-09-23
State when frozen: no scientific outcome/expectancy/PnL has been computed.

## Frozen beta-return definition

For every Binance 1H candle with open_time H:

`r_1h(H) = ln(close(H) / open(H))`

The event at boundary T uses:
- signal candle H = T-1h;
- beta estimation excludes H=T-1h;
- beta window is the preceding 720 hourly candles H=T-721h through T-2h inclusive;
- use paired BTC/ALT candle returns only;
- require >=684 valid paired rows;
- OLS includes intercept; only the slope beta is used in the residual;
- residual at the event = ALT signal-candle return - beta * BTC signal-candle return.

No close-to-close beta, no EWMA beta, no no-intercept regression, no shorter/longer window after outcomes.
