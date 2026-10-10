# LICP-001 — HYPERLIQUID REAL-TIME LIQUIDATION SOURCE AUDIT V0.1

Date: 2026-09-26
Status: NO DOCUMENTED MARKET-WIDE LIQUIDATION WEBSOCKET IDENTIFIED

## Official WebSocket documentation reviewed
Hyperliquid mainnet WebSocket:
- wss://api.hyperliquid.xyz/ws

Official subscription types include public market feeds such as:
- allMids
- l2Book
- trades
- bbo
- activeAssetCtx / allDexsAssetCtxs

The documented liquidation object appears under:
- userEvents
which requires a specific user address.

The official subscription list does not document a market-wide all-liquidations stream analogous to Bybit allLiquidation.

## Scientific consequence
Do not silently substitute Hyperliquid userEvents for a complete market-wide liquidation firehose.

For LICP-FWD-XALT-004:
- historical event source remains Hyperliquid complete archive evidence;
- live source-transfer implementation remains Bybit BTCUSDT allLiquidation primary + Binance forceOrder confirmation;
- this source-transfer difference is an explicit risk and must be tested forward on MEXC.

## Allowed Hyperliquid live context
Public allMids / bbo / l2Book / activeAssetCtx may be used for contextual market/OI information when causally collected.

They do not independently prove a complete liquidation trigger.

Sources:
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket
