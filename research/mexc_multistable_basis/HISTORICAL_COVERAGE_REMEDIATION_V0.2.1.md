# MEXC-MULTI-STABLE-BASIS-001 — HISTORICAL COVERAGE REMEDIATION V0.2.1

Date: 2026-10-07
Status: SOURCE-ONLY / OUTCOME-BLIND

Parent V0.2 result:
- COVERAGE_PARTIAL
- frozen monthly anchors 2026-05-01 through 2026-09-01 failed for all required contract and normalization routes
- 2026-10-01 passed
- zero OHLC values, basis, returns or PnL opened

Purpose:
Determine the exact recent-history availability boundary without changing any economic hypothesis, because no economic hypothesis has yet been opened.

Frozen probe dates, UTC 00:00-01:00:
- 2026-09-07
- 2026-09-10
- 2026-09-14
- 2026-09-17
- 2026-09-21
- 2026-09-24
- 2026-09-28
- 2026-10-01
- 2026-10-04
- 2026-10-06

Frozen routes:
- BTC_USDT / BTC_USDC / BTC_USD1
- ETH_USDT / ETH_USDC / ETH_USD1
- USDCUSDT / USD1USDT
- USD1USDC consistency route

Record only transport success, row/timestamp counts, first/last timestamps, hashes and latency.
Do not report or calculate OHLC values, basis, returns, funding economics or PnL.

Historical SOURCE PASS requires at least 60 consecutive calendar days of exact 60/60 minute coverage across all mandatory six contracts plus USDCUSDT and USD1USDT. The consistency route USD1USDC is diagnostic only.

If the proved common window is <60 days, classify:
HISTORICAL_SOURCE_BLOCKED_INSUFFICIENT_COMMON_COVERAGE

Do not shrink the 60-day requirement after seeing results.

Prospective continuation remains scientifically separate and may be frozen later if current public feeds remain source-valid.
