# CRYPTO LAB — CONVEX V03 BINANCE HISTORICAL L1 EXECUTABLE-ENTRY SOURCE GATE — PRE-OUTCOME FREEZE
Date 2026-10-17 UTC. Branch isolated from PR #246. Science/research-only. No real trading, no accounts, no broker private endpoints, no Render or Windows changes, no main merge, no 2026 holdout.

## External source justification and limitations
Official GitHub Binance public data issue #334 says historical USDⓈ-M bookTicker stopped publication after 2024-03-30, so there exists a BOUNDED source opportunity from 2023-05-16 through 2024-03-30. See https://github.com/binance/binance-public-data/issues/334 . Raw archive family:
https://data.binance.vision/data/futures/um/daily/bookTicker/{symbol}/{symbol}-bookTicker-{YYYY-MM-DD}.zip and sibling .CHECKSUM. This is Binance futures top-of-book data, not Kraken/OKX/MEXC execution. No reason to port commissions or fills.

## Frozen sample selection, outcome blind to PnL
Read EXACT original completed and immutable source run 38432883246 (canonical 8ALT 3Y source) without opening sealed 2026.
- SOLUSDT 1h BASE trade ledger and BNBUSDT 4h BASE trade ledger.
- From each original ledger select EXACTLY the first TWO original trades by `open_t` in interval `2023-05-16T00:00:00Z <= open_t < 2024-03-31T00:00:00Z`. No filter by PnL, win/loss, funding, trading outcome, slip, venue spread, or convenient source availability. Same exact timestamps can be reused for STRESS only as a separate descriptive timing comparison; **do not select new dates** if source blocked.
- If 0/1 eligible trades exist, return SAMPLE_INSUFFICIENT with exact count; do not substitute more active strategy, months or date windows.
- On each selected entry UTC date request ONLY its daily official bookTicker ZIP and matching .CHECKSUM, no more than 4 days (duplicate dedup), no GET to exchange API, maximum ZIP 85MB, maximum CSV uncompressed 500MB, timeout 35 sec. No retry/region bypass on HTTP errors.

## Chronology and schema gates, frozen before response
- Check publisher SHA256 for each downloaded ZIP (strict 64-hex field); one CSV member, `update_id,best_bid_price,best_bid_qty,best_ask_price,best_ask_qty,transaction_time,event_time` required or aliases strictly mapped and logged, no ambiguity. Verify timestamps are milliseconds, within selected UTC date, nondecreasing; no nonpositive or crossed best prices, quantities positive. Never interpolate.
- For each original entry at `open_t`, obtain only the most recent SOURCE event with `event_time <= open_t` (strictly past-only). Source age thresholds: <= 2000ms primary, 2000-10000ms sensitivity only, >10000ms SOURCE_STALE. Do not use future event or next candle. Any same-timestamp repeated event: last update_id in raw event chronology only if monotonically ordered.
- Compare original simulated filled entry price (already includes 2 bps slip BASE) to **bid/ask top of book** and original trade quantity. For LONG, executable direction ASK, but top-of-book is not a guaranteed fill. Show simple price difference bps vs original modeled entry and whether quoted ASK quantity meets original qty; do not infer iceberg/multi-level/rejections. Record latest bid/ask, update ID, quote age, noncross, publisher checksum, count events. If quote age bad -> no price comparison.
- No downstream exit rewrite, no funding recomputation, no stop replay, no hindsight stop entry, no backtested new PnL. L1 single timestamp + quantity is an EXECUTION OBSERVATION, not certified counterfactual fill. Any quote since prior date omitted may be stale, mark invalid.

## Outcomes
`SOURCE_BLOCKED` (missing/stale/corrupt archive), `BOOK_QUOTE_CAUSAL_CANDIDATE` (fresh top bid/ask for one selected original trade), `TOP_OF_BOOK_SIZE_INSUFFICIENT` (fresh quote, inadequate depth at first level), `SAMPLE_INSUFFICIENT` (fewer than two prior eligible entry timestamps). All missing must be reported. Never output an alpha or trading approval even on successful source checks.

## Explicit prohibitions
No price optimization, no modification of original V5, no transfer of original Binance returns to Kraken or OKX, no account login, API secrets, orders, leverage, exchange mutation, spending, protected 2026 data or merge to main. Existing six historical BASE/STRESS ledgers remain immutable. This newly opened source is retrospective already-selected history and receives ZERO OOS CREDIT.

**Pre-source/final science authority:** NO TRADING GO. All endpoints fixed to official publisher data, with 4 max eligible dates deterministically chosen before quote receipt.
