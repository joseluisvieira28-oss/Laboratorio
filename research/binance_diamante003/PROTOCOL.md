# BINANCE-DIAMANTE-003 — CONTINUOUS SPOT DEPTH SOURCE & REPLAY
**PRE-SOURCE FREEZE:** 2026-11-23, isolated branch; RESEARCH ONLY, NO CAPITAL, NO TRADES.

## Fixed question / limitation
Can one **bounded live public** Binance Spot WebSocket capture provide gap-safe, independently replayable local orderbooks for BTCUSDT, ETHUSDT and SOLUSDT? Also collect aggressive `aggTrade` records without claiming that depth updates identify actual order cancellations, absorption or predictive alpha. The goal is SOURCE/INTEGRITY ONLY. A future economic hypothesis requires an **independent LAB_ID and pre-registration**; no future price PnL read here.

## Frozen source scope (before observation)
- Exactly 3 Spot assets `BTCUSDT`, `ETHUSDT`, `SOLUSDT`; exactly one anonymous combined public WS connection to `wss://data-stream.binance.vision/stream?streams=btcusdt@depth@100ms/btcusdt@aggTrade/ethusdt@depth@100ms/ethusdt@aggTrade/solusdt@depth@100ms/solusdt@aggTrade`.
- Default WS payload timestamps in milliseconds; one **45-second** live frame window; no reconnect, no retries, no cron or recurring job; maximum 12,000 messages and 20 MB journal; if limit reached early, classify `CAPTURE_TRUNCATED` not success.
- For **each asset**, buffer diff-depth frames before one public REST snapshot: `https://data-api.binance.vision/api/v3/depth?symbol=<S>&limit=1000`. Strictly three possible REST GETs, no credentials. Bounded 2 MB response and 15 s timeout; no HTTP451 workaround, region/proxy bypass, paid feeds or alternate sources.
- Journal each exact UTF-8 WebSocket frame and exact REST JSON response with collector arrival UTC nanoseconds, monotonic nanoseconds, SHA-256 of raw bytes and hash-chain per sequential frame; prevent silently discarding raw messages. Must be independently replayable.
- Binance Spot reconciliation: ignore diff with `u <= snapshot.lastUpdateId`; first retained event must cover `snapshot.lastUpdateId+1` within `[U,u]`. For any live diff with `U > local_id+1`, mark irreversible **GAP_SOURCE_BLOCKED**, never repair from unverified later frames; if `u <= local_id` ignore stale. Non-monotone update IDs, malformed or crossed book fail closed. Depth quantities of zero mean level removal from current visible book; **NOT proof of a canceled order**. Snapshot initially max 1000/side, book beyond remains UNKNOWN.
- Reproduce original journal byte hashes/chain and independently rebuilt per-symbol applied depth counts, last update ID, aggregate trade counts, source/buffer/gap statuses; no signal/outcome data or PnL.

## Acceptance
`SOURCE_REPLAY_PASS_ONLY` needs: single complete 45 sec window (within 3 s slack), all 3 snapshots bridged correctly and updated at least 10 diffs, all three `aggTrade` streams seen, zero gaps/parse/crossed-book errors, journal under bound, and independent replay exact match. Otherwise report `SOURCE_BLOCKED_OR_INSUFFICIENT`. A green CI is NOT economic edge and does NOT prove Swiss account eligibility, exact execution, queue position, full depth, or persistent 24/7 reliability.

## Baselines and lessons
- `BINANCE-001 PR #372` verified 3 official 1m archive ZIPs and official checksums; no trading edge.
- `BINANCE-002 PR #373` validated 3 REST snapshots and 100 aggTrades each; 10bps fee-per-side hypothetical costs 19.98 to 21.36 bps roundtrip at 1000 USDT. Static snapshot not continuous book.
- `BTC10m Spot/Perp flow PR #313` **NO EDGE** 2025 OOS; NOT rescued or retuned.
- Other frozen labs, protected outcomes and main untouched. No production, Telegram, Render, API keys, balances, trading, deposits, wallets, subscriptions, fees, futures activation or merges.

## Causal interpretation ceiling
**Book removal is not cancellation.** **Aggressor flow is not itself a forward return forecast.** **Trade events and book diffs have separate clocks and cannot be causally matched by arrival order alone.** This experiment does NOT compute buying/selling signals, absorption signatures, market impact PnL or prospective statistical significance. A follow-on novel hypothesis is allowed only after audit of actual source continuity, independent mechanisms and frozen holdout rules.

Official Binance Spot sources: https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md ; https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md
