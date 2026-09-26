# DEFI-LIQUIDATION-SHOCK-001 — MARKET DATA SOURCE GATE FREEZE V0.1

Date: 2026-09-27
Status: FROZEN SOURCE-SELECTION RULE / OUTCOME-BLIND
Market outcomes remain CLOSED.

## Purpose

Freeze market-data source precedence and integrity rules before any event return is computed.

A venue/source cannot be chosen because its reaction to liquidations is stronger.

## Required data

- direct market for the prospectively mapped target asset;
- 1-minute UTC OHLC bars;
- complete required Discovery/OOS interval for each included market segment;
- bar OPEN is the only field required by the primary return definition;
- volume may be retained descriptively but is not a primary outcome.

## Source precedence

### Priority 1 — Binance public Spot archive

Authority route:
Binance public-data / data.binance.vision Spot 1-minute kline archive.

Use DAILY 1m archives as the canonical archive unit for this lab.

For every downloaded archive:
- retrieve companion CHECKSUM;
- verify SHA256 before parsing;
- require exact UTC 1-minute open timestamps;
- reject duplicate open timestamps;
- reject non-monotonic bars;
- report missing minute count.

Monthly archives are not primary authority for this lab.

### Binance reconciliation

Use Binance Spot REST kline endpoint only for deterministic reconciliation samples and source diagnostics.

For each accepted symbol/year:
- select a deterministic source-only sample of archived open timestamps;
- query the same 1m bars by start/end time;
- require open price/open timestamp exact equality under the numeric canonicalization rule frozen by implementation.

Archive/API conflict:
MARKET_DATA_SOURCE_CONFLICT_FAIL_CLOSED

REST is not used to silently patch an archive conflict.

### Priority 2 — OKX direct Spot historical candles

Only if no adequate Binance direct market exists for the target asset.

Use OKX public historical candlestick source at 1m.

Required:
- exact instrument identity;
- UTC timestamp normalization;
- completed historical candles only;
- reproducible pagination;
- no authenticated/private account data;
- full required date coverage under the same missingness gate.

OKX cannot replace a valid Binance mapping because it produces a more favorable outcome.

### No third-source rescue in V0.1

If neither frozen source can provide a direct historically defensible market:
MARKET_MAPPING_UNAVAILABLE

Do not add Coinbase/Kraken/DEX/proxy sources after outcome access.

A third source requires a new authority while outcomes are still closed.

## Pair/quote selection

Pair selection is availability-based only.

Preferred quote order:
1. USDT
2. USD
3. USDC

Within a source, choose the first quote in this order with source-proven coverage for the required interval.

If only the inverse of a direct stable-asset pair exists, reciprocal price transformation is allowed only when the exact same two assets form the pair.

No correlated proxy.

## Asset identity

Allowed direct mapping:
- exact source-authoritative token/asset identity;
- native SOL <-> canonical wrapped SOL equivalence;
- Drift market index -> frozen historical underlying identity.

Any other wrapped/bridged/staked/derivative token requires its own direct market unless a separate source authority proves economic identity.

Examples that are NOT automatically interchangeable:
- mSOL vs SOL
- JitoSOL vs SOL
- bridged ETH token vs native ETH
- LP token vs components

## Historical listing boundary

A market is eligible only during the interval for which the venue/source proves bars exist.

Do not backfill a token with a later-listed market.

A cluster before the market's first source-proven bar is:
MARKET_MAPPING_UNAVAILABLE_FOR_EVENT_TIME

## Delisting / symbol migration

Symbol text is descriptive, not identity authority.

If a venue changes symbol or delists/re-lists:
- preserve source timestamps and product identity;
- freeze a source-only lineage before using multiple symbols/products as one market;
- otherwise split or mark unavailable.

## Time normalization

All timestamps normalized to UTC.

Primary 1m bar key:
bar open timestamp.

No local-time exchange display convention may change the UTC bar key.

## Data integrity

For every accepted market/source interval report:
- expected minute range;
- observed bars;
- duplicate count;
- non-monotonic count;
- missing bar count;
- checksum status when source provides checksums;
- deterministic reconciliation sample result.

No silent forward-fill for missing OPEN prices.

## Coverage gate

The missingness thresholds in OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1 are mandatory.

Source/market mapping is decided before event/control returns are inspected.

If coverage is inadequate:
MARKET_DATA_SOURCE_BLOCKED

It is not NO_EDGE because the hypothesis was not validly tested.

## Protected period

Do not download or inspect 2025/2026 bars for this experiment.

Allowed market-data window ends strictly before:
2025-01-01T00:00:00Z

## Current documentation evidence at freeze

Binance official public-data repository documents:
- Spot kline archives;
- 1m interval support;
- programmatic archive downloads;
- companion CHECKSUM verification.

Binance Spot API documentation defines 1m klines keyed by open time with UTC start/end parameters.

OKX public API documentation defines historical candlesticks, 1m bars, pagination by timestamp and completed-candle state.

These references establish route feasibility only. Actual per-market historical coverage remains a later SOURCE FEASIBILITY gate.

## Firewall

market_bars_downloaded=false
prices_inspected=false
returns_computed=false
pnl_computed=false
economic_outcomes_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
