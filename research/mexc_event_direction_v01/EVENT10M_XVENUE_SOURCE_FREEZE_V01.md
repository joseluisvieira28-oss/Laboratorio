# EVENT10M CROSSVENUE AS-OF FEASIBILITY V0.1 — PRE-CAPTURE FREEZE
Date 2026-10-30. Study identifier E10M-XVENUE-RECEIPT-001. Source-only, no economic outcomes.

## Distinct economic question, and hard anti-duplication
Prior Event Futures studies: PR #277 continuous 3m aggressor sign vs MEXC 10m index HISTORICAL NO_EDGE, PR #107 forced liquidation cascade terminal NO_EDGE, PR #289 Event Futures two-sided 10m payout no-arbitrage, PR #275 probability calibration gate blocked. THESE are NOT rerun, rescued or renamed.
New source mechanism is **prospective cross-venue receipt timing**, not a price model or an empirical trading signal. Evaluate feasibility of public Binance USD-M BTC/ETH aggTrade receipt and MEXC public BTC/ETH Event Futures index receipt on the same GitHub Actions runner with independently preserved UTC and monotonic timestamps. No optimization of direction or price thresholds; no label/return; no headline event training; no September 2026 holdout. NVIDIA separate chat and excluded.

## Frozen public sources
(1) Binance USD-M BTCUSDT and ETHUSDT public aggTrade websocket, documented combined stream: wss://fstream.binance.com/market/stream?streams=btcusdt@aggTrade/ethusdt@aggTrade . Event field E is event time, T trade time, m buyer-is-maker; st if present identifies UM. This is trade flow in a *different venue* and market, not a cash/index equivalence.
(2) MEXC established Event Futures page public-index channel: wss://futures.mexc.com/edge ; outbound messages ONLY {"method":"sub.index.price","param":{"symbol":"BTC_USDT"}} and same ETH, with matching public UNSUB; require channel push.index.price and numeric data.price, optional exchange "ts". No account, login, API key, private channels, Event Futures orders, REST order, payments or Telegram send.
- Run bounded 45 seconds after starting concurrent sockets; no session/geo bypass, no alternative domains or exchange substitutes if source blocked. At most 10,000 processed Binance frames, 2,000 MEXC frames, no unlimited retry.
- Record actual receive timestamp from same process in UTC milliseconds AND monotonic nanoseconds; event/source timestamp separately, hashes for raw frames. A source exchange ts vs local receipt ts difference is **NOT** calibrated one-way network latency without synchronized clocks. Source timestamps may be stamped at other stages. No pings interpreted as trading signals.
- Per-symbol source pass requires >=20 Binance valid aggTrade frames AND >=2 MEXC valid public index ticks in observation and >=20 seconds joined socket observation. This is a source gate only, no guarantee of continuing availability at market-event times.
- Output counts, first/last UTC, source errors and shared-process observed MEXC-index tick vs Binance **previous local receive age** and Binance-trade vs MEXC most recent tick local age (never "market lead" conclusion). Absence of update cannot prove absent price information; content timing and index formula are different. Do not compute profitability/forward returns from these source samples.
- Print min/median/p95 of receipt-age, aggregated per symbol; preserve samples in immutable run artifact for audit. No public server clock accuracy assumed; report actual data and discard invalid timestamps.
- Explicit human-alert feasibility GATE BLOCKED: no Telegram delivery, human read time, exchange acceptance/position opening or final true Event Futures price/expiry. Receiving a public index is not receiving a contract fill. Estimate none of these from pings; fail closed.
- Independent causal probability evaluation must be SEPARATELY preregistered *after* source gate, with a previously trained model, locked rule and 30-calendar-day prospective batch >=150 independent non-tie observations per symbol and horizon plus matched baseline, costs, Holm/block bootstrap, and independent custody. No test of any such outcome in V0.1.

## Verdict semantics
SOURCE_FEASIBLE (both symbols both venues) or SOURCE_BLOCKED/PARTIAL_SOURCE. Both are compatible with ZERO CERTIFIED EDGE. A source PASS does not authorize live trading or research target opening. No automatic trading API for MEXC Event Futures should be assumed. No merges to main, costs or orders.

References:
- Binance USD-M aggTrade source documentation https://developers.binance.info/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Mini-Tickers-Stream
- MEXC existing validated WS capture research/mexc_event_futures/public_index_source_v0121.py and V0121_CLOSEOUT_PUBLIC_INDEX_STREAM_PASS.md
- PR #275 causal offline gates and forward sample floor.
