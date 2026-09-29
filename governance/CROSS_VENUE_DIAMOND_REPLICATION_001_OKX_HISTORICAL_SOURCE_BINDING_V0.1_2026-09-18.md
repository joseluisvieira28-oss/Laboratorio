# CROSS-VENUE-DIAMOND-REPLICATION-001 — OKX HISTORICAL SOURCE BINDING V0.1 — 2026-09-18

Status: FROZEN_BEFORE_HISTORICAL_ARCHIVE_PAYLOAD_ACCESS
Branch: cross-venue-diamond-replication-001-donchian6h
Candidate: HTF-DONCHIAN DH-02-HO1 6H

## Authority recovered from official OKX SDK

Official repository: okxapi/python-okx
File: test/test_public_data.py
Observed blob SHA: 79e5d350d9ee7b30de27301f40c11c875bae4286

The official SDK test documents the historical-market-data server enum:
- module 1 = Trade history
- module 2 = 1-minute candlestick
- module 3 = Funding rate
- module 5 = 5000-level orderbook
- module 6 = 50-level orderbook
- dateAggrType = daily or monthly
- instType includes SWAP

This source binding therefore fixes, before archive payload access:

PRICE SOURCE:
- endpoint: /api/v5/public/market-data-history
- module: 2
- semantic type: 1-minute candlestick
- instType: SWAP
- dateAggrType: monthly

FUNDING SOURCE:
- endpoint: /api/v5/public/market-data-history
- module: 3
- semantic type: funding rate
- instType: SWAP
- dateAggrType: monthly

Frozen instruments:
- BTC-USDT-SWAP
- ETH-USDT-SWAP
- SOL-USDT-SWAP
- BNB-USDT-SWAP
- XRP-USDT-SWAP
- DOGE-USDT-SWAP

Frozen source period:
- 2023-01-01T00:00:00Z inclusive
- 2025-01-01T00:00:00Z exclusive
- calendar years 2025 and 2026 forbidden

## Acquisition contract

1. Request monthly historical packages independently for module 2 and module 3.
2. Persist request timestamp/status/provider metadata for every instrument/month/module.
3. Do not substitute mark-price, index-price, spot, futures delivery, or another quote currency.
4. After provider files become available, preserve original bytes and calculate SHA256 before parsing.
5. Candlestick payload must prove monotonic UTC minute timestamps and no duplicate timestamp.
6. Funding payload must preserve actual provider funding timestamps and rates; no interpolation or synthetic funding.
7. Canonical 15-minute signal bars must be generated deterministically from the provider's exact 1-minute trade-price candles, matching the parent semantics.
8. Trade paths must be resolved on 1-minute candles using the exact parent execution logic.
9. No signal/return/PnL calculation until complete price + funding source validation passes for the frozen venue.

## Current venue state

OKX:
- exact 6Hutc/1m anchor coverage for all six frozen instruments in 2023-2024: PASS from source-only probe
- historical archive server enum: RESOLVED
- exact archive payload access: NOT YET OPENED under this binding

BYBIT:
- public mainnet transport from current GitHub-hosted US runner: BYBIT_SOURCE_BLOCKED_ENVIRONMENT
- this is not an economic rejection

## Governance

research_only = true
outcome_blind_at_freeze = true
no_2025_outcomes = true
no_2026_outcomes = true
no_live_trading = true
no_exchange_mutation = true
no_authenticated_exchange_api = true
no_orders = true
no_wallets = true
no_alerts_webhooks = true
no_merge_to_main = true
no_post_outcome_tuning = true
