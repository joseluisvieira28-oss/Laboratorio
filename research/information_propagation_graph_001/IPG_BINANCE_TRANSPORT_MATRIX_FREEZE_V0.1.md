# IPG-001 BINANCE PUBLIC TRANSPORT MATRIX FREEZE V0.1

Frozen: 2026-09-24
Stage: FORWARD SOURCE TRANSPORT REMEDIATION ONLY

Trigger:
The first public forward source smoke passed all three Deribit streams but:
- Binance Spot stream.binance.com:9443 returned HTTP 451;
- Binance USD-M Futures fstream.binance.com returned no aggTrade event before timeout.

No IPG outcome was opened.

## Official routes under test

Spot WebSocket:
1. wss://stream.binance.com:9443/ws/btcusdt@aggTrade
2. wss://stream.binance.com:443/ws/btcusdt@aggTrade
3. wss://data-stream.binance.vision/ws/btcusdt@aggTrade

Binance documents data-stream.binance.vision as a market-data-only WebSocket endpoint.

Spot REST diagnostics only:
- https://data-api.binance.vision/api/v3/aggTrades?symbol=BTCUSDT&limit=5

USD-M Futures WebSocket, same documented fstream host but different official
subscription shapes:
1. raw URL /ws/btcusdt@aggTrade
2. combined URL /stream?streams=btcusdt@aggTrade
3. base /ws then SUBSCRIBE btcusdt@aggTrade

Futures REST diagnostic only:
- https://fapi.binance.com/fapi/v1/aggTrades?symbol=BTCUSDT&limit=5

## PASS semantics

Spot transport PASS requires >=3 valid realtime aggTrade WebSocket events from
at least one official Spot WebSocket route.

Futures transport PASS requires >=3 valid realtime aggTrade WebSocket events
from at least one official USD-M Futures WebSocket route.

REST diagnostics can explain reachability but can never satisfy the forward
WebSocket timing gate.

No venue substitution, no Binance.US, no testnet, no authenticated streams.
