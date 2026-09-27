# LICP-001 — MEXC 2025 HISTORICAL COVERAGE SOURCE GATE V0.1

Date: 2026-09-26
Status: SOURCE COVERAGE ONLY — NO PRICE OUTCOMES

Purpose:
Test whether public MEXC Futures Min1 kline history is accessible for BTC_USDT, ETH_USDT and SOL_USDT during the external Hyperliquid liquidation-study window in 2025.

Probe windows:
- 2025-08-10 UTC
- 2025-10-10 UTC
- 2025-12-31 UTC

The probe reads only timestamp coverage/counts from the response.
OHLC values are not analyzed or reported.

PASS_SAMPLE requires non-empty minute timestamp coverage for all three target symbols in all probe windows.

Passing this gate would establish historical target-source feasibility only.
It would not authorize use of any external event table as Crypto Lab OOS evidence.
