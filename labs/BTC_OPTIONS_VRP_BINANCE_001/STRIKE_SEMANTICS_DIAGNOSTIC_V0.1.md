# BTC-OPTIONS-VRP-BINANCE-001 — STRIKE SEMANTICS DIAGNOSTIC V0.1

Date: 2026-09-19
Parent diagnostic: `BOVRP-BINANCE-GEOMETRY-ZERO-DIAG-001`
Parent run: `35463137570`

The parent diagnostic proved every 08:00 row on all three frozen dates reaches the strike parse step and fails there:
- 2023-05-18: 248 / 248
- 2023-07-01: 280 / 280
- 2023-10-23: 230 / 230

This diagnostic may expose only source identity semantics needed to interpret the strike field: the exact normalized header map plus up to 10 unique raw strike tokens and corresponding symbol/type tokens from the original first frozen sample date. No bid/ask prices, IV outcomes, returns, VRP or PnL may be emitted.

Any parser correction requires a separate frozen technical amendment.
