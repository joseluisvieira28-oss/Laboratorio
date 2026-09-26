# DEFI-LIQUIDATION-SHOCK-001 — MARKET DATA MAPPING REGISTRY FREEZE V0.1

Date: 2026-09-27
Status: FROZEN / OUTCOME-BLIND / METADATA-ONLY

## Purpose

Define the only admissible registry format that can map MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS targets
to the market-data sources frozen in MARKET_DATA_SOURCE_GATE_FREEZE_V0.1.md.

No mapping may be chosen using a future return, price response, volatility or PnL.

## One row per target identity

Every unique target from MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json must have exactly one registry row.

Fields:

- target_identity
- status:
  - BINANCE_DIRECT
  - OKX_DIRECT
  - MARKET_MAPPING_UNAVAILABLE
- canonical_asset_id
- identity_authority: non-empty list of source-only references that bind the source target identity to the canonical asset
- notes

### BINANCE_DIRECT

Required:
- symbol
- base_asset
- quote_asset
- venue_metadata_authority
- listing_start_utc or explicit SOURCE_NOT_AVAILABLE
- archive_route_template
- checksum_route_template

Quote asset must respect:
USDT > USD > USDC

A lower-priority quote requires explicit source-only evidence that higher-priority quotes are unavailable for the required period.

### OKX_DIRECT

Allowed only if Binance direct coverage is not adequate under frozen precedence.

Required:
- instrument_id
- base_asset
- quote_asset
- venue_metadata_authority
- listing_start_utc
- historical_candle_route_authority
- binance_unavailable_evidence

### MARKET_MAPPING_UNAVAILABLE

Required:
- reason
- evidence

It is forbidden to substitute a correlated proxy.

## Identity standard

Symbol equality alone is not sufficient for a Solana mint.

For `mint:<pubkey>`, identity_authority must include source evidence binding that exact mint to the canonical asset.

For Drift:
- historical market-index authority may bind index -> source asset identity;
- subsequent venue mapping must bind that asset to the venue product.

Wrapped/staked/LP/derivative assets are NOT automatically equivalent to the underlying.

## Inferential dependency

Any target marked inferential_dependency=true in MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json
must have BINANCE_DIRECT or OKX_DIRECT.

A descriptive-only target may be MARKET_MAPPING_UNAVAILABLE with evidence.

## No price payload

This registry and its validation may use:
- product/instrument metadata;
- listing/delisting metadata;
- contract/mint identity metadata;
- archive object metadata/HEAD;
- checksum object metadata/HEAD.

It may not open OHLC/candle payloads.

## Firewall

archive_payload_downloaded=false
candles_opened=false
prices_opened=false
returns_computed=false
pnl_computed=false
economic_outcomes_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
merge_main=false
