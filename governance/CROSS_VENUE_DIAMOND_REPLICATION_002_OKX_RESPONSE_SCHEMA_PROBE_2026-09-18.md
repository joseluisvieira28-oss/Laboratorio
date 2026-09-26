# CROSS-VENUE-DIAMOND-REPLICATION-002 — OKX HISTORICAL RESPONSE SCHEMA PROBE — 2026-09-18

Status: FROZEN_BEFORE_SCHEMA_PROBE_AND_BEFORE_HISTORICAL_PAYLOAD_ACCESS

Candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1
Venue: OKX AVAX-USDT-SWAP
Endpoint: /api/v5/public/market-data-history

## Purpose

The bounded historical-source shape gate established that module 2 (candlestick) and module 3 (funding rate) accept the frozen AVAX-USDT historical request, but the metadata-only sanitizer intentionally suppressed unrecognized fields.

Before any historical file or market value is opened, this gate inspects only response schema.

## Frozen request

- module: 3 only
- instType: SWAP
- dateAggrType: monthly
- begin: 2025-01-01 inclusive
- end: 2025-02-01 exclusive
- instFamilyList: AVAX-USDT

## Allowed observations

- HTTP status
- provider code/message
- number of response rows
- sorted key names present in each response row
- JSON value type for each key
- for nested objects/arrays: nested key names/types only

Values MUST NOT be persisted except provider code/message and structural counts.
No URL may be followed.
No price, funding rate, timestamp payload, return, signal or PnL value may be persisted or calculated.

## Routing

If schema exposes a provider file/download/status field, freeze a separate exact payload acquisition contract before following it.
If schema contains historical data rows directly, freeze a separate exact parser/source-validation contract before opening values.
If neither route is structurally identifiable, classify SOURCE_BINDING_UNRESOLVED and stop.

2026+ remains forbidden. Research only. No live trading, orders, exchange mutation, wallets, alerts/webhooks or main merge.
