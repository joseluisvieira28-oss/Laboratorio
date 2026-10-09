# Technical Kraken candle HTTP end-boundary clarification — 2026-10-09

Original public source scan on GitHub Actions run **37940261621** returned 25 candles on several fixed 2023/2025 date windows, because the public chart API may include the next midnight bar in an inclusive `to` bound. V01 mechanical test required **all returned timestamps** to equal the 24 exact in-day timestamps, so it marked those samples `DAY_BARS_PARTIAL_OR_INVALID` even if the same response contains all 24 intended in-day stamps.

This is **not an economic strategy change** and no 2021-2025 outcomes are optimized. Technical fix frozen before replay:
- Keep original symbols `PF_ETHUSD/PF_SOLUSD/PF_BNBUSD`, exact 3 fixed source dates `2021-06-15 / 2023-06-15 / 2025-06-15`, original URL `/trade/{symbol}/1h?from=...&to=...&count=48` and no alternate date or market selection.
- Define a daily source gate PASS only if **the subset with** `day_start_ms <= bar_timestamp < next_day_start_ms` equals exactly all 24 expected hourly timestamps. Separately record count of outside-day extra bars, duplicate timestamps, 1h numeric OHLC validation and report if first sample actually lacked requested date. Never fabricate missing timestamp.
- Date 2021 missing bars remains `SOURCE_BLOCKED`; Kraken source even with later-day PASS cannot be promoted to complete 2021–25 execution, and 2023 public ORDER EVENTS do not reconstruct archived best bid/ask/depth without immutable order book state.
- Re-run both unchanged canonical economics and this source correction in an isolated workflow. No account/trading/main/2026 holdout access, no changed economic figures.
