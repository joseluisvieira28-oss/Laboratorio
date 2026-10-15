# TradingView Paste Runbook — SRC Crypto Lab Institutional Flow V1

1. Open TradingView.
2. Open `BINANCE:BTCUSDT`.
3. Set timeframe to `1D`.
4. Open Pine Editor.
5. Paste the complete contents of `tradingview/SRC_Crypto_Lab_Institutional_Flow_V1.pine`.
6. Save as `SRC Crypto Lab — Institutional Flow V1`.
7. Click `Add to chart`.
8. Do not modify signal logic if TradingView reports a mirror mismatch.

## Acceptance gate

The indicator is accepted as an exact TradingView research mirror only if:

- Pine v6 compiles unchanged.
- dashboard shows `PASS — 50/50`;
- `Mirror faults = 0`;
- first signal marker is 2025-01-15;
- last signal marker is 2025-12-24;
- 2026 displays `LOCKED — NO SIGNALS` and no post-2025 signal markers appear.

If compilation fails, record the exact compiler message and line number. Syntax/API compatibility fixes are permitted only when they do not alter the frozen mechanism. If the structural gate fails after successful compilation, stop: classify it as a TradingView mirror/data-alignment failure rather than changing timing or signal rules.
