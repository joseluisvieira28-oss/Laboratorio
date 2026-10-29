# TRIPLE FLOW V0.2 — SOURCE RECOVERY / FORWARD TRANSPORT PROOF
2026-10-29. FROZEN BEFORE THIS V0.2 DATA COLLECTION.
State: SOURCE_ONLY. NO OUTCOMES, NO ECONOMIC MODEL, NO EDGE, NO LIVE TRADING.

## Parent immutability
Parent PR #278 at d13364ee4fbddc24ca75cdff78ee64d7baa8c1b9 remains SOURCE_INCOMPLETE. Its April 1 six Tardis files (7,945,015 records), MD5/SHA checksums, 12 near-midnight book exchange timestamps and unknown liquidation feed continuity remain canonical. DO NOT edit the parent freeze, reinterpret it as passing, or open price outcomes on V0.1. PR #107 BTC60s liquidation cascade terminal NO_EDGE -16.374554bps remains CLOSED, unaltered.

## Scope A — new archive DAY PARTITION semantics only
Tardis official downloadable CSV documentation states daily file partitioning uses LOCAL_TIMESTAMP (collector receive time). Historical 2026-04-01 files may include events with exchange timestamps just before midnight if their collector local_timestamp occurs after midnight. This is SOURCE semantics, not an outcome parameter.
The new V0.2 archive boundary permits exchange_time before midnight solely when 2026-04-01 LOCAL receive timestamp is in range and 0 <= (local - exchange) <= 5 seconds; all exchange times must be causal <= received. Preserve exact defect rows; no drop, rewrite, source substitution, or original V0.1 waiver. For this first pass ONLY re-evaluate previous signed evidence/defect receipts; the full 7.9M raw source bytes are not re-downloaded so the strongest label is METADATA_BOUNDARY_RECONCILED, not FULL_SOURCE_PASS.
No evidence is available that a normalized liquidation CSV without disconnect heartbeats contains a complete all-day liquidation event census. Empty intervals remain UNKNOWN, never ZERO.

## Scope B — independent new read-only live transport probe
Bybit mainnet PUBLIC linear market websocket wss://stream.bybit.com/v5/public/linear.
Exactly six topics: publicTrade.BTCUSDT and ETHUSDT, orderbook.50.BTCUSDT and ETHUSDT, allLiquidation.BTCUSDT and ETHUSDT. No auth/login. No other symbols.
One websocket with one subscribe; 95-second single continuous capture, 15-second public app-ping cadence, no auto-reconnect. Raw messages hashed in a deterministic rolling SHA256; preserve bounded per-topic counts, local receive timestamps, UTC 5-second coverage, orderbook snapshot+sequence/restart checks, observed events only, pong and subscription receipts. No outcome-price source, no MEXC Event Futures payouts, no signal/feature model, no order/account/private API.
Pass transport-health demonstration ONLY if socket remains connected >=90s, subscribe acknowledges, >=4 pong frames, at least 70% of closed 5-second buckets have each symbol's PUBLIC TRADE and BOOK data, book snapshots arrive, and there are zero errors. If connection fails: fail closed. Observed liquidation events count as observed; absence of messages is UNKNOWN, not a certified zero. A websocket heartbeat and visible activity show transport liveness, not proof of absolute completeness of exchange liquidation messages, sequence-free liquidation feed or any historical Tardis capture.
Promote neither model nor economic edge, even if transport probe passes.

## Later data gate
To permit a prospective flow+forced-liquidations+depth experiment, require (a) continuously timestamped as-of public collector on same clock with health bins, pongs, errors, disconnections and no-event unknowns; (b) objective source-quality criteria, enough verified positive liquidation episodes, strict cross-feed freshness for each model candidate; (c) exact contemporaneous MEXC payout/index receipts. Design and freeze the model+ablation and baselines BEFORE accessing any future outcomes. Holdout September 2026 is closed. Live orders/account/keys/private endpoints/paid services and main merge prohibited.
References: https://docs.tardis.dev/downloadable-csv-files ; https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation ; https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook ; https://bybit-exchange.github.io/docs/v5/websocket/public/trade .
