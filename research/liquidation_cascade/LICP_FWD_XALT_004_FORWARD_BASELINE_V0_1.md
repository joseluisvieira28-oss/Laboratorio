# LICP-FWD-XALT-004 — FORWARD BASELINE V0.1

Date: 2026-10-08

## State
**FORWARD_INSUFFICIENT**

Canonical forward run `37309426462` produced four matured, complete SOL_USDT 60-minute
episodes under the frozen BTC-liquidation ignition -> SOL SHORT transfer rule.

- completed: **4/4**
- missing: **0**
- distinct UTC dates: **1**
- mean net after frozen 16 bps hurdle: **-11.2958 bps**
- median gross: **+18.8394 bps**
- date mean gross (2026-10-05): **+4.7042 bps**

Per-event net:
- **+23.1504 bps**
- **+10.7782 bps**
- **-5.0994 bps**
- **-74.0124 bps**

This is not a terminal verdict. The prospective freeze requires at least 20 independent episodes
across at least 3 UTC dates with <=10% missing rate.

The historical XALT-003 holdout remains a separate historical survivor. This forward baseline
tests live-source/MEXC transferability and cannot be rescued or overwritten by the historical result.
