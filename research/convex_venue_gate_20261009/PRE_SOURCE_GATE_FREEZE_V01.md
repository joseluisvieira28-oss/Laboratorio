# BTC CONVEX — VENUE HISTORICAL BBO / DEPTH / FUNDING / CONTRACT SOURCE GATE — FROZEN 2026-10-09

## Mission and hard authority
Operator authorized attacking exact **historical execution feasibility** of original Parent V5 ETH/SOL/BNB, 2021-01-01 through 2025-12-31. All prior historical results are known; no new virgin OOS inference. Start from successful official original source/raw reproduction run 37916963862 and official 1-minute STOP gate 37917719450. Historical positive first basket remains scope-limited; failed 13-asset expansion remains failed.

**No live trading, orders, private market/account API, wallet keys, spend, protected 2026 outcomes or merge.** All API requests here are unauthenticated public GET/HEAD only.

## Exact economic evidence required
1. Distinguish **MEXC FUTURES executable venue** from Binance original backtest historical venue. Binance quote data are only proof that a *Binance* historical quote stream existed; they do NOT transfer to MEXC.
2. For each of ETH_USDT/SOL_USDT/BNB_USDT: probe:
   - Public MEXC `GET https://contract.mexc.com/api/v1/contract/depth/{symbol}?limit=20` for L2 snapshot CURRENT ONLY; record HTTP/parsed timestamps, BBO, best displayed size and 2026 observation age; **do not use them to populate 2021-25 fills**.
   - Public MEXC `GET /api/v1/contract/detail/country?symbol=...` for contractSize, minVol, volUnit, max market-order size, API trading allowed, fee fields when present, country restrictions unknown.
   - Public MEXC `GET /api/v1/contract/funding_rate/history?symbol=...&page_num=1&page_size=1000` for list length, oldest/newest timestamps, `totalPage`; if page count within reasonable 1..1000 and validated, test final page for earliest available official funding; fail-closed if oldest cannot be verified.
   - No fake historical orderbook query. Document official `depth_commits` last N, not archive.
   - If geo/rate limited/403 mark ACCESS_BLOCKED, not missing market history.
3. Binance USD-M **official** `bookTicker` archives: fixed source gate **each** of ETHUSDT/SOLUSDT/BNBUSDT for **2021-01-02, 2023-05-24, 2024-01-15, 2025-06-17, 2025-12-01**; public HEAD for file status/ContentLength/LastModified with GET fallback (Range request) only for server HEAD 405 or 403, avoid downloading giant archives just to determine file presence. Document status and cache headers. Archived bookTicker format expected seven fields: update_id, best_bid_price, best_bid_qty, best_ask_price, best_ask_qty, transaction_time, event_time. Existing Binance community warning some 2024 files contain out-of-order observations: impose sorting by event time and update ID before any historical joins.
4. After HEAD gate, make **one** deterministic low-cost actual payload probe only: Binance official ETHUSDT 2025-12-01 (if archival HEAD confirms HTTP 200 and content-length <= 80MB) and additionally ETHUSDT 2024-01-15 only if first probe size <=20MB. Verify archive ZIP SHA256 against official CHECKSUM URL when available, parse first actual 1000 non-header rows, enforce bid >0, ask>=bid, positive quantities, timestamps normalizable 2025 or 2024, report min/max, spread quantiles, negative/crossed count and monotonicity. Report anomalous, out-of-order rows instead of rewriting hidden.
5. Historical first basket entry/exit matching NOT authorized from only one sampled arbitrary file; do not claim execution-level PnL or economic approval from this source feasibility. For a second distinct full-trades experiment, freeze sampling at original chronological signal timestamps first, use all relevant files and quote staleness/quantity criteria. Not performed unless supported within available resources and re-frozen.

## Cost/size bound and categories
- Original Binance Parent BASE 10bps fee per side + 2bps slip per side = 24bps fixed roundtrip drag; STRESS 30bps plus original funding. Historical source venue Binance.
- MEXC official 2026-05-28 announcement, effective 2026-06-01 08:00 UTC, **Futures API taker 8bps per side** (16bps fee roundtrip); quote spread, market impact and funding **additional**. Do not treat original Binance 24bps vs MEXC 16bps as a free +8bps arbitrage.
- Current MEXC snapshot can show physically displayed top-level volume but cannot be used for historical timestamp fill, and the third array field in public depth format may count orders, not asset units. Without proven contractSize+volUnit and corresponding timestamp depth, notional market impact is UNVERIFIED.
- Official MEXC historical funding `funding_rate/history` may be paginated; timestamp coverage, missing events and mark prices must be verified, **no using Binance funding as MEXC funding**.

## Frozen verdict schema
Every source gate produces independent status:
- `MEXC_HISTORICAL_BBO_2021_2025`: PASS only if exact downloadable/public original-period BBO with bid/ask/size/timestamps for every chosen 2021-25 trade instant; otherwise `SOURCE_NOT_ESTABLISHED`, not "no such dataset exists" globally.
- `MEXC_FUNDING_HISTORY`: PASS_COMPLETE only with start/end required actual timestamps and coverage; else PARTIAL_OR_BLOCKED.
- `MEXC_PUBLIC_CONTRACT_AND_NOW_QUOTES`: ACCESS_PASS/ACCESS_BLOCKED, NOT historical proof.
- `BINANCE_BOOKTICKER_SOURCE_PROBE`: PASS/INCOMPLETE/BLOCKED with exact 15 HEAD response matrix; `SAMPLED_BBO_PAYLOAD_PROVEN` only with parsed ZIP and checksum evidence.
- `EXACT_MEXC_EXECUTION_NET_EDGE`: ALWAYS UNVERIFIED unless actual timestamped target-venue executable BBO+depth and fees/funding reconstructed for original full sample, never inferred from public endpoint docs.
- `LIVE_GO`: NO.
- This source feasibility scan cannot weaken or upgrade previous BTC Convex local historical PASS / global 13 asset FAIL and does not open 2026 OOS.

## Source authority hyperlinks (2026)
MEXC official depth https://www.mexc.io/api-docs/futures/market-endpoints/get-contract-order-book-depth
MEXC official funding history https://www.mexc.io/api-docs/futures/market-endpoints/get-funding-rate-history
MEXC official contract detail https://www.mexc.io/api-docs/futures/market-endpoints/get-contract-info
MEXC API fee bulletin https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742
MEXC last-N snapshot API https://www.mexc.io/api-docs/futures/market-endpoints/get-the-last-n-depth-snapshots
Binance official archive https://data.binance.vision/ and README https://github.com/binance/binance-public-data
Binance bookTicker sample structure / out-of-order warning https://github.com/binance/binance-public-data/issues/305
