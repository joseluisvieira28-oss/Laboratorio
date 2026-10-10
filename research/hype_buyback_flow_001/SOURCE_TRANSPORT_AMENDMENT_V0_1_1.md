# HYPE-BUYBACK-FLOW-001 — SOURCE TRANSPORT-ONLY AMENDMENT V0.1.1
Date: 2026-10-10 UTC. Status: pre-probe correction, source-only.
Original source freeze: SOURCE_GATE_AUTHORITY_V0_1.md (commit 71d4d33fe73c0a91d266ce23410d9cd63a33733d).
Run 38040251218: 3 synthetic tests PASS; public spotMeta PASS; userFillsByTime returned HTTP error.
Run 38040320526: same result; HTTP 422, body 'Failed to deserialize the JSON body into the target type'; SHA256 6448c95b4fb0147552cb0c95b53f9b5e5ff810da3c115d9e61c7c49430894a31.
No HYPE price outcomes inspected, no fees/cost models changed, no edge hypothesis/promotions.

TRANSPORT-ONLY variants predeclared BEFORE these new calls:
- A: `{"type":"userFillsByTime","user":AF,"startTime":NOW_MS-3600000}` (minimal schema, 1 hour only).
- B: `{"type":"userFills","user":AF}` (public official AF system address; recent only).
- C: `{"type":"recentTrades","coin":"@107"}` (market-level public HYPE/USDC trades; inspect whether `users[0]` equals AF, the buyer position, for any trade; DO NOT interpret trade taker `side` as wallet buy/sell without actual user binding).
The official market identity was source-proven, before variant C, by spotMeta 2026-10-10. Do not substitute unrelated market.
Store request and response SHA256/UTC/HTTP status/roundtrip. Limit 8MB per body. No performance / price return / PnL / backtesting.
No changes to original 90-day contiguous complete corpus source PASS threshold or historical 10k cap. Any single recent API response is only a source probe, not evidence for an hour/day historical pace or net profitability.
An HTTP 422 can be a schema error, not proof the fund did not buy. An HTTP 200 with an empty list can be unsupported system-account mapping, retention or simply no recent eligible fills; do not claim zero buybacks.
NO AWS/S3, account access, wallets, credentials, Render or trading.
Official source evidence:
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions
