# DEFI-LIQUIDATION-SHOCK-001 — V0.2 FUTURES ARCHIVE IDENTITY ADDENDUM V0.1

Date: 2026-09-29
Status: FROZEN SOURCE-GATE ADDENDUM / BEFORE FUTURES PRICE PAYLOAD ACCESS

## Problem

The GitHub runner may be unable to reach Binance USD-M REST exchangeInfo because of transport/geographic restrictions.

Transport unavailability is not a product-identity contradiction.

## Historical product identity fallback

For V0.2 development, BINANCE USD-M SOLUSDT perpetual historical source identity may pass without live exchangeInfo only if all are true:

1. source is the official Binance public-data USD-M Futures hierarchy:
   data/futures/um/;
2. exact archive symbol is SOLUSDT;
3. exact interval is 1m;
4. exact DAILY kline archive route is used;
5. companion CHECKSUM exists for every deterministic metadata probe;
6. archive + checksum HEAD probes return HTTP 200 across every frozen quarterly probe spanning the development interval;
7. official Binance public-data documentation identifies futures/um as USD-M Futures and futures kline archives as /fapi/v1/klines-derived data;
8. no conflicting reachable product metadata is observed.

If exchangeInfo is reachable and contradicts SOL / USDT / PERPETUAL identity:
DLS_V0_2_FUTURES_SOURCE_BLOCKED.

If exchangeInfo is unreachable but all seven historical archive criteria pass:
HISTORICAL_ARCHIVE_PRODUCT_IDENTITY_PASS.

This rule is frozen before any V0.2 futures archive is downloaded or decompressed.

## Firewall

futures_price_payload_opened=false
2025_opened=false
2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
