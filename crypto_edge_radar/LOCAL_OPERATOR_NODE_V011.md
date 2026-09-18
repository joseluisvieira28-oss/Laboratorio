# LOCAL OPERATOR NODE V0.11

Status: **PUBLIC SHADOW ONLY / NO CAPITAL / NO ORDERS**

V0.11 extends the V0.10 Windows node with a second always-on local timing process.

## Local processes

1. **DH03 12H collector**
   - Binance USD-M public WebSocket only.
   - 1m + 15m + mark-price/funding observation.
   - Local SQLite durability.
   - Scientific forward outcomes remain governed by the checksum-verified archive reconciliation path.

2. **BNB Launchpool fast monitor**
   - Binance official public CMS GET-only discovery.
   - BNBBTC public spot market-data binding.
   - 30-second polling floor.
   - Separate local evidence database and status file.
   - This is detection/shadow infrastructure only. It cannot create an order.

3. **Loopback Radar dashboard**
   - http://127.0.0.1:8787
   - Public/read-only operational state.

## Local files

- data/bnb_local_status.json
- data/bnb_local_evidence.sqlite3
- DH03 market/evidence databases under the existing CryptoEdgeRadar local-data path.

## Hard safety

- no API keys
- no authenticated exchange API
- no POST/order endpoint
- no wallet access
- no live capital
- no leverage mutation
- no automatic micro-live authorization

A running V0.11 node improves public-event detection latency. It **does not** itself remove the separate execution-authority, fee, venue-state, or account-state blockers.
