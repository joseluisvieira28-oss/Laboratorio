# CROSS-VENUE-DIAMOND-REPLICATION-002 — OKX HISTORICAL SOURCE BINDING V0.1

Status: FROZEN_BEFORE_HISTORICAL_ARCHIVE_PAYLOAD_ACCESS
Branch: cross-venue-diamond-replication-002-avax20
Candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1

## Recovered provider authority

The sibling cross-venue source investigation recovered the official OKX historical market-data server contract from the OKX SDK:
- endpoint: /api/v5/public/market-data-history
- module 2 = 1-minute candlestick
- module 3 = funding rate
- dateAggrType = monthly
- instType = SWAP

This binding is frozen before any archive payload is followed or parsed.

## Exact AVAX source binding

Instrument: AVAX-USDT-SWAP

PRICE:
- endpoint: /api/v5/public/market-data-history
- module: 2
- semantic type: 1-minute trade-price candlestick
- instType: SWAP
- dateAggrType: monthly

FUNDING:
- endpoint: /api/v5/public/market-data-history
- module: 3
- semantic type: funding rate
- instType: SWAP
- dateAggrType: monthly

Frozen source months:
- warmup: 2024-09 through 2024-12
- replication: 2025-01 through 2025-12
- 2026+ forbidden

## Source-only acquisition gate

Before signal/return/PnL:
1. Request provider metadata for every frozen month independently for module 2 and module 3.
2. Persist request month/module, HTTP/provider code, provider status/state metadata and source fingerprint.
3. Do not follow or download archive URLs during the metadata gate.
4. Do not inspect OHLC or funding-rate payload values during the metadata gate.
5. Full historical replication is authorized only after complete monthly price + funding packages are source-valid.
6. Once payload access is separately frozen, preserve original bytes and SHA256 before parsing.
7. Price payload must prove monotonic UTC minute timestamps, no duplicates and parent-compatible complete-day reconstruction.
8. Funding payload must preserve exact provider timestamps/rates; no interpolation or synthetic funding.

No substitution of spot, mark/index price, another quote currency, another venue, another timeframe or synthetic data.

## Current venue routing

OKX:
- AVAX-USDT-SWAP instrument existence: PASS
- 1m anchor coverage across warmup/full replication period: PASS
- ordinary funding-history endpoint for old anchors: insufficient historical reach
- historical monthly archive route: now frozen for source metadata gate

BYBIT:
- both official mainnet REST hosts return HTTP 403 from current GitHub-hosted runner environment
- classification: BYBIT_SOURCE_BLOCKED_ENVIRONMENT
- not an economic rejection

## Governance

research_only = true
outcome_blind = true
no_2026_plus = true
no_live_trading = true
no_orders = true
no_authenticated_exchange_api = true
no_wallets = true
no_exchange_mutation = true
no_execution_webhooks = true
no_post_outcome_tuning = true
no_main_merge = true
