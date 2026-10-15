# BTC-OPTIONS-VRP-BINANCE-001 — BTCUSDT SPOT 1M SOURCE CLOSEOUT V0.1

Date: 2026-09-19
Probe: `BOVRP-BINANCE-SPOT1M-SOURCE-001`
Canonical run: `35463357528`
Canonical head: `1c7dc47d5f7be1b61a23aa119d81c4a92ae5113b`

## Final classification

**BINANCE_SPOT1M_SOURCE_FEASIBLE**

All three frozen dates passed:
- 2023-05-18: 1,440 rows, 08:00 UTC bar present;
- 2023-07-01: 1,440 rows, 08:00 UTC bar present;
- 2023-10-23: 1,440 rows, 08:00 UTC bar present.

The source is the public Binance BTCUSDT spot 1-minute archive and requires no account, API key or payment.

## Scientific meaning

This binds a zero-cash-cost point-in-time underlying source for a later independently frozen Binance-options volatility study.

It does not authorize:
- realized variance computation;
- option/spot returns;
- VRP;
- PnL;
- performance tuning;
- 2025/2026 outcomes;
- live trading or exchange mutation.

The source pass only removes a data-provenance blocker.
