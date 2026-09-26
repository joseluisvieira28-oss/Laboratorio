# LICP-001 — MEXC MULTI-ASSET TARGET SOURCE GATE V0.1

Date: 2026-09-26
Status: SOURCE ONLY

Target symbols:
- BTC_USDT
- ETH_USDT
- SOL_USDT

Purpose:
Prove that all three intended target books can be observed concurrently with public MEXC Futures depth streams.

PASS_SAMPLE per symbol requires:
- subscription acknowledged
- >= 20 depth updates
- zero crossed reconstructed BBO
- zero local clock regressions
- zero version regressions

No returns, labels, thresholds, or PnL are computed.
