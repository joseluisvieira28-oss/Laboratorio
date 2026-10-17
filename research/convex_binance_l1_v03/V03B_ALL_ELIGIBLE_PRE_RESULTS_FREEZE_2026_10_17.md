# CONVEX V03B — FULL ELIGIBLE BOOKTICKER COVERAGE — PRE-RESULT FREEZE
Date: 2026-10-17 UTC. This document and frozen sample-selection rules are committed BEFORE accessing any remaining 2023–2024 entry quote results beyond V03's first two chronological trades per lane.

## Evidence context and full population
Canonical original run 38432883246, Binance official 2023-25 V5 frozen BASE ledgers. Pre-known V03 source-only verified:
- SOLUSDT 1h: 33 eligible original trades opened from 2023-05-16 to 2024-03-30 inclusive (of 84 total original closes).
- BNBUSDT 4h: 6 eligible original trades opened in same fixed window (of 28 original closes).
Original V03 4 earliest historical entry probes resulted 2 causal quote+size candidates, 1 fresh but insufficient best-ASK size, and 1 missing prior quote. No new trading claim.

## Immutable expansion
- NO retrospective PnL or trade-success filtering; select **ALL** original BASE entries with UTC entry start at/after 2023-05-16T00:00Z and strictly before 2024-03-31T00:00Z, all 33 SOL / all 6 BNB. Block if expected counts differ; do not change source range, trade order or asset.
- Read exact same two original artifact ZIPs, exact source statuses SHA/112-file publisher manifests from original V03. Duplicate UTC dates fetched once, ordered chronologically.
- For each selected date, read original official daily `bookTicker` publisher ZIP with sibling .CHECKSUM using unchanged strict original V03 `fetch_archive` / `last_causal_quotes` source parser: one request per URL, no retries, maximum 85 MB compressed, 500 MB uncompressed, 8m events, quote timestamp <= entry time, age <=2000ms.
- **Keep every episode**, whether it passes, fails, is source-inaccessible, expired, stale, has insufficient quantity or appears to contradict the backtest. Write per-signal receipt `BOOK_QUOTE_CAUSAL_CANDIDATE`, `TOP_OF_BOOK_SIZE_INSUFFICIENT`, `SOURCE_NO_PRIOR_QUOTE`, `QUOTE_2S_TO_10S_SENSITIVITY_ONLY`, `SOURCE_STALE_OVER_10S`, `SOURCE_BLOCKED`, and publish full denominator. No later lookahead quote filling.
- Same symbol bookTicker size is only **best ASK size at latest event**, not cumulative depth, guaranteed fills, order queue or stop. No venue portability. Any successful source observation is IN-SAMPLE infrastructure evidence only.
- Source feasibility thresholds, frozen prior to expansion: >=95% of selected entries have fresh <=2s past-only quote with official valid publisher hash; >=90% of such fresh entries have quoted single best-ASK quantity >= original modeled BASE trade quantity. Ineligible source periods remain **SOURCE_ROUTE_INSUFFICIENT** not strategy NO-EDGE. Both assets assessed separately; zero favorable subset selection.
- Report distribution of ask-vs-modeled-entry bps separately for fresh entry candidates and fresh insufficient-depth events: count, median, min/max, worst positive difference, no PnL, no alternative fee schedules, no exit re-model. Don't mark an executable market fill or economic promotion from this.
- Stop broker attached ACK remains unverified and does not become verified by market-data receipts. Original 2026 holdout remains locked. No orders, wallets, private endpoints, paid data, Render, Windows mutations or main merge.

This is full **historical Binance L1 source** population, **not** MEXC/Kraken/OKX. OOS alpha authority NONE, LIVE GO NONE. If Binance publisher stops providing data or budgets hit the fixed per-file cap, classify the full population with missing receipts and stop: no bypass and no substitution.
