# DLS V0.2 — BINANCE USD-M ARCHIVE IDENTITY FALLBACK ADDENDUM V0.1

Date: 2026-09-28
Status: FROZEN PRE-PAYLOAD SOURCE-TRANSPORT ADDENDUM

## Trigger

The first V0.2 execution source probe observed:
- 37/37 deterministic monthly SOLUSDT USD-M Futures daily archive objects present;
- 37/37 companion CHECKSUM objects present;
- the live fapi exchangeInfo route was unreachable from the GitHub runner after retries.

This is metadata transport unavailability, not historical archive absence.

## Authority

The official Binance public-data repository documents:
- market type `um` = USD-M Futures;
- USD-M Futures kline archives are sourced from `/fapi/v1/klines`;
- daily archives and companion CHECKSUM files are official public data.

For V0.2 development source identity only, the exact archive namespace:

data/futures/um/daily/klines/SOLUSDT/1m/

plus deterministic archive+CHECKSUM existence across every month from 2021-12 through 2024-12 is sufficient to establish the historical development route when live fapi metadata is transport-unavailable.

## Fail closed

This fallback is allowed only if:
- all 37 frozen monthly probes pass archive + CHECKSUM existence;
- live metadata returned no contradictory product metadata;
- symbol is exactly SOLUSDT in the USD-M Futures archive namespace.

Any explicit metadata contradiction blocks.

## Scope

Development historical-data source only.
Does not establish:
- MEXC live venue equivalence;
- live trading authority;
- current executable contract parameters;
- 2025/2026 access.

2025_opened=false
2026_opened=false
live_trading=false
orders=false
merge_main=false
