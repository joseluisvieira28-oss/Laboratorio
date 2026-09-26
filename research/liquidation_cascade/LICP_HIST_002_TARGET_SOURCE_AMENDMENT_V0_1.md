# LICP-HIST-002 — TARGET-SOURCE AMENDMENT V0.1

Date: 2026-09-26
Status: PRE-OUTCOME TECHNICAL AMENDMENT

The initial Bybit V5 historical REST source probe returned HTTP 403 for all six fixed 2025 control requests from the GitHub runner.

No historical target-price outcome was opened.

The historical cross-venue target source is therefore changed from Bybit REST to the official Binance Public Data archive (Binance Vision), USD-M Futures 1-minute klines.

This does NOT change:
- the external Hyperliquid event source;
- the causal observable trigger time = t0 + 5 minutes;
- the allowed external fields = t0 + symbol only;
- the future continuation hypothesis;
- any outcome horizon.

Target symbols:
- BTCUSDT
- ETHUSDT

Fixed source-control months:
- 2025-08
- 2025-10
- 2025-12

No price values are inspected in the source gate.
