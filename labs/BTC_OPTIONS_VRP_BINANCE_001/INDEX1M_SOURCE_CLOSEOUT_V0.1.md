# BTC-OPTIONS-VRP-BINANCE-001 — BTCUSDT INDEX 1M SOURCE CLOSEOUT V0.1

Date: 2026-09-19
Probe: `BOVRP-BINANCE-INDEX1M-SOURCE-001`
Canonical run: `35466189046`
Canonical head: `f2b053e68af75179eabc7a82a886b7c6e97f4181`

## Final classification

**BINANCE_INDEX1M_SOURCE_FEASIBLE**

All three frozen dates downloaded and parsed with a valid 08:00 UTC bar:
- 2023-05-18
- 2023-07-01
- 2023-10-23

The public archive is available without account, API key or cash payment.

The source receipt reported 1,441 CSV rows per sample because the archive includes a header record; the timestamp parser ignores that non-numeric header, so this is a transport-format detail rather than an extra market minute.

## Scientific meaning

The exact point-in-time Binance BTCUSDT index source required by the pre-frozen option-fee/moneyness protocol is now available at zero cash cost.

No option return, spot/index return, realized variance, VRP or PnL was computed in this source gate.
