# DEFI-LIQUIDATION-SHOCK-001 — MARKET DATA ROUTE METADATA PROBE FREEZE V0.1

Date: 2026-09-27
Status: FROZEN / OUTCOME-BLIND / NO CANDLE PAYLOAD

## Preconditions

- SOURCE_SAMPLE_GATE_PASS
- MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS
- MARKET_DATA_MAPPING_REGISTRY_PASS

## Binance metadata probe

For every BINANCE_DIRECT target:

1. query public Spot `exchangeInfo` for the frozen symbol;
2. require exact symbol, baseAsset and quoteAsset match the frozen registry;
3. never query ticker/price endpoints;
4. for each frozen `monthly_probe_date` at or after the source-supported listing boundary:
   - HTTP HEAD the frozen DAILY 1m archive ZIP;
   - HTTP HEAD the companion CHECKSUM object;
5. never GET/decompress the archive body.

A monthly probe date is the earliest source cascade T0 calendar date in that target/month.
It is frozen from source events, not market outcomes.

For an inferential target:
- all applicable monthly metadata probes must exist;
- otherwise MARKET_DATA_SOURCE_BLOCKED.

For a descriptive-only target:
- route gaps are reported but cannot create an inferential claim.

## OKX metadata probe

For every OKX_DIRECT target:

1. query only the public SPOT instruments metadata endpoint;
2. require exact instrument id, baseCcy and quoteCcy;
3. require the frozen historical-candle documentation authority and Binance-unavailability evidence;
4. do NOT call history-candles before FINAL_PRE_DISCOVERY_AUTHORITY_PASS because that response contains OHLC payload.

The listing boundary from source metadata must be compatible with the frozen registry.

## MARKET_MAPPING_UNAVAILABLE

No venue request is made.

Inferential_dependency=true + unavailable => MARKET_DATA_SOURCE_BLOCKED.

## PASS

MARKET_DATA_SOURCE_PASS requires:
- mapping registry PASS;
- every inferential target direct-mapped;
- every inferential Binance target product metadata exact;
- every inferential Binance monthly ZIP+CHECKSUM HEAD probe PASS;
- every inferential OKX target product metadata exact and frozen route authority present;
- zero source identity conflicts;
- no candle payload opened.

This is route feasibility only. Full candle checksum/content QA happens only after
FINAL_PRE_DISCOVERY_AUTHORITY_PASS.

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
