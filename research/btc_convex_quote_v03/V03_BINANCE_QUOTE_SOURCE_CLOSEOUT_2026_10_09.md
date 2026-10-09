# BTC-CONVEX V0.3 — BINANCE OFFICIAL USD-M QUOTE SOURCE CLOSEOUT
Date: 2026-10-09
Mode: Public GET only / scientific source probe / no capital.
Workflow https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37886368656
Freeze commit d1ce5764afb5f98ac9087b93fa0e55a903d7623c ; runner commit 319d319337054a996af1d12ae0875e7757c2bf83 ; artifact 11596760653.

## Fixed original source
https://fapi.binance.com/fapi/v1/time ; /fapi/v1/exchangeInfo ; /fapi/v1/depth?symbol=...&limit=20. Fixed BTCUSDT/ETHUSDT/SOLUSDT/BNBUSDT and $10/$25/$50/$100 fictitious scenarios. No keys or orders.

## Results
- Python compilation passed; six synthetic fail-closed tests passed.
- First live GET to Binance USD-M `/fapi/v1/time` returned **HTTP 451** in GitHub Actions.
- Zero real venue depth responses, zero admissible quote samples, zero scored signal/entry/exit outcomes.
- Workflow concluded failure intentionally; artifact and full blocker preserved. Neither an unauthorized alternative Binance host nor a substituted venue was used to count a PASS.
- HTTP 451 is consistent with a geographically/legal restricted response; do NOT presume legal access, and do NOT evade access restrictions.

## Verdict
**SOURCE_BLOCKED_NO_TRADING** on this exact GitHub Actions environment and frozen endpoint. Not a strategy NO_EDGE, not a statement about BTC-CONVEX economic viability, and not a venue-wide or Swiss legal conclusion.
The original V0.2 prospective work remains separate and FORWARD_INSUFFICIENT. Quote and exact next-bar-open executable fill proof: NOT AVAILABLE.
No main change, no real trading, no capital, no exchange mutation.
