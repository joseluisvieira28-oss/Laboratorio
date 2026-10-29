# Joint flow + liquidation + visible depth: source gate V1
2026-10-29. SOURCE ONLY, no directional outcome protocol activated.
Parent PR277 head 4006749653f6521a15c5b893710ada1d8543ba2e; audit PR107 head 418e94638aaecd1a6c8289cad116c829bf748bbb.

## Frozen scope before full file parsing
Exactly Bybit BTCUSDT and ETHUSDT, UTC 2026-04-01 only (already exposed Discovery).
Free unauthenticated Tardis CSV: trades, liquidations, book_snapshot_5.
No alternative dates/symbols/providers after inspecting quality. HTTP availability is not PASS.
No MEXC index/payout/forward outcome requests; no September 2026 request.
Keep HEAD404 and GET206 evidence separately. No GitHub Actions or paid compute.

## Gates
Complete gzip parse and CRC, positive sizes/prices, exact symbol/exchange, microsecond UTC timestamp range within day, nondecreasing collector local_timestamp; preserve duplicate rows, never deduplicate identical liquidation events blindly.
SHA256 of full compressed files, byte counts and provider x-md5 equality where provided.
Trades require buy/sell taker sides. Liquidations require buy/sell forced-order sides; verify normalization against provider mapping, not raw Bybit position side.
Books require all 5 levels on both sides, sorted positive uncrossed.
At least 99% UTC minute coverage for trades and books; no assumption that liquidation absence is zero if feed continuity cannot be independently established.
All streams p99(local_timestamp - timestamp) between 0 and 5 seconds; report negative lag count and raw max rather than hide tails.
Quality diagnostics may read feature timestamps, sides, sizes and levels, but must not join to future returns or compute directional performance.
No raw exchange sequence IDs/heartbeat ledger in normalized CSV: distinguish an archive replay feasibility pass from a verified complete causal liquidation census.

## Acceptance
HISTORICAL_PROXY_SOURCE_PASS only if all files validate, timing and coverage gates pass AND liquidation continuity/normalization is defensible. Otherwise SOURCE_BLOCKED or SOURCE_INCOMPLETE, no outcome protocol and no economic study.
This does not establish live source custody or cancellation causality. Top5 depletion is a displayed-liquidity proxy; executions, price-level migration and cancellation are not separately identified.

## Existing hypotheses retired / not rescued
PR107 terminal closeout (not stale PR body): NO_EDGE, first20 BTC60s, 18 valid, mean base -16.374554bps, stress -32.374554bps. Do not reopen or reverse it.
PR277 3m continuous aggressor sign: 0/4 positive hypothetical EV at q80%; q85% BTC30m singleton cannot be selected.
Prior static L2 and LVAC 2023 sample, failed absorption count gate remain unchanged.
Only incremental joint conditioning could justify a distinct later exploratory rule, with component ablations, all cells and fixed horizons before outcomes. No protocol is activated here.

Primary references:
- https://github.com/joseluisvieira28-oss/Laboratorio/pull/107
- https://github.com/joseluisvieira28-oss/Laboratorio/pull/276
- https://github.com/joseluisvieira28-oss/Laboratorio/pull/277
- https://docs.tardis.dev/historical-data-details/bybit
- https://docs.tardis.dev/downloadable-csv-files/data-types
- https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation
- https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook

No orders/accounts/authentication/private exchange endpoints/wallets/spend/main changes/merge.
