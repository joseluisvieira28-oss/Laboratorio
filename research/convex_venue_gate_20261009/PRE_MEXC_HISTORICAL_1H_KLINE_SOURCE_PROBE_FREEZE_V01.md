# BTC CONVEX — MEXC HISTORICAL 1H PERPETUAL KLINE SOURCE PROBE V0.1 FREEZE — 2026-10-09

Read-only historical price-source test, frozen before querying MEXC. Market OHLCV can never substitute historical target-venue bid/ask/depth, stop fills or 2021-2025 MEXC funding. No new OOS/trading/live orders/main merge/private endpoints.

Use ONLY public GET `https://contract.mexc.com/api/v1/contract/kline/{symbol}` for all three exact original instruments `ETH_USDT`, `SOL_USDT`, `BNB_USDT`.
Request `interval=Min60` and exact UTC day 00:00–23:59:59 in UNIX SECONDS for each of the following independently frozen probes:
- 2021-06-15 (early-market source)
- 2023-06-15 (mid source)
- 2025-06-15 (later historical source)
Exactly 9 requests total; no interval, date or symbol replacements if missing. Expected 24 unique hourly timestamps within the UTC day with finite OHLC and nonnegative volumes, o>0, l<=o/c<=h.
If endpoint responds with latest candles, wrong timestamps or partial times, report `SOURCE_INVALID_FOR_REQUESTED_DAY`, not historical coverage. Record SHA256 each public response, status and 24/24 completeness.
Request MEXC history based on supplied open/close series. Do not infer whether original 2021-25 43,824 exact hours are fully covered from just nine day-probes; status `PROBED_DATE_COVERAGE_ONLY`.
Do not conflate Binance original futures funding, historical MEXC funding earliest 2025-04-17 in V01, or Binance bookTicker 2023/24 source with this MEXC 1h venue price evidence.
If early date 2021 fails, record MEXC_1H_EARLY_SOURCE_BLOCKED, without imputing missing data. If all dates pass, MEXC_PRICE_SAMPLE_SOURCE_PASS only. True full executable MEXC net edge remains UNVERIFIED.
