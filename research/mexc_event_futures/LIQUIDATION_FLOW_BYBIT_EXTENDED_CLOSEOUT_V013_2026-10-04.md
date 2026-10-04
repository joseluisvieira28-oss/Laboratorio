# LIQUIDATION-FLOW-FWD-001 — BYBIT EXTENDED SOURCE CLOSEOUT

Date: 2026-10-04
Authoritative source observation run: 37075262340
Artifact id: 11257963990
Artifact SHA256: `1521ef40603b46a3e76fc148c1e6df9d830faae7c00030ed720e23c45c3e1a5f`

## Frozen observation

Source:
- Bybit public liquidation WebSocket
- BTCUSDT and ETHUSDT
- duration: 3600 seconds
- source-only
- no Event Futures outcomes

## Result

`PARTIAL_SOURCE`

Subscription acknowledgement: PASS

Valid real events:
- BTCUSDT: 3
- ETHUSDT: 0

BTC events preserved with raw SHA-256 and exchange timestamps:
1. Sell, size 0.004, bankruptcy price 84733.00
2. Sell, size 0.008, bankruptcy price 84769.80
3. Sell, size 0.001, bankruptcy price 84808.50

Errors: 0

Safety:
- NO_AUTH: true
- NO_PRIVATE: true
- NO_ORDERS: true
- NO_ACCOUNT_READS: true
- NO_MEXC_OUTCOMES: true

Research outcomes opened: 0
Active family: 0

## Interpretation

This is NOT a NO_EDGE verdict.

The run proves that the Bybit source can deliver valid real BTC liquidation events with the expected side/size/bankruptcy-price/timestamp fields.

It does not pass the pre-registered two-symbol source gate because ETH produced zero valid events.

It is also far below the frozen calibration minimum of >=100 nonzero healthy bins per symbol.

## Versioning consequence

`LIQUIDATION-FLOW-FWD-001` remains unchanged and inactive.

Any OKX source work is a separate source version:
`LIQUIDATION-FLOW-FWD-002`

No venue pooling is authorized and Bybit observations may not be merged into OKX calibration.
