# DEFI-LIQUIDATION-SHOCK-001 — SAVE11 OFFICIAL API LOCATOR CALIBRATION FREEZE V0.1

Date: 2026-09-23
Status: FROZEN PRE-EXTRACTION / SECONDARY LOCATOR ONLY / OUTCOME-BLIND / FAIL-CLOSED

Provider:
Save/Solend official API `https://api.solend.fi`

Route:
`GET /history-v2/liquidation-attempts`

Prior schema-only probe:
- run `35917129116`;
- 5 / 5 probe variants returned JSON 2xx;
- observed record schema exposes at least `signature`, `slot`, `success`, and `timestamp`;
- no economic field values were retained by the probe.

## Frozen calibration window

`[2024-07-19T19:30:52Z, 2024-07-20T00:00:00Z)`

This is exactly the already frozen first Save 0x11 census chunk.

Known RAW-verified boundary control:
- signature `WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L`
- slot `278496102`
- timestamp `1721417452`

## Extraction contract

Request exactly:
`/history-v2/liquidation-attempts?start=1721417452&end=1721433600`

Recursively inspect the JSON structure and retain only objects containing all four scalar keys:
- `signature`
- `slot`
- `success`
- `timestamp`

Persist ONLY those four fields. Do not persist fee payer, market, reserve, token, amount, value, balance, price, USD or user/account identifiers.

Timestamp handling is frozen prospectively:
- integer-like Unix seconds are accepted directly;
- integer-like Unix milliseconds are divided by 1000 exactly;
- anything else fails closed.

Filter locally to the frozen half-open interval regardless of server-side query handling.

Deduplicate by signature:
- identical duplicate records collapse deterministically;
- conflicting slot/success/timestamp for one signature => fail closed.

The known RAW boundary signature MUST be present or the locator calibration fails.

## Interpretation firewall

This API is a **secondary candidate locator only**.

A locator row is NOT an authoritative Save 0x11 event and MUST NOT enter the realized-event population unless exact on-chain program + tag `0x11` RAW verification passes.

Even 100% recall on this calibration chunk does NOT authorize replacing exhaustive source coverage for the full historical window. Any future use beyond secondary cross-checking requires a separately frozen completeness policy.

Classifications:
- `SAVE11_OFFICIAL_API_LOCATOR_CHUNK_PASS`
- `SAVE11_OFFICIAL_API_LOCATOR_BOUNDARY_MISS`
- `SAVE11_OFFICIAL_API_LOCATOR_SCHEMA_FAIL_CLOSED`
- `SAVE11_OFFICIAL_API_LOCATOR_TRANSPORT_BLOCKED`

Firewalls:
prices=false; amounts=false; balances=false; usd_values=false; returns=false; pnl=false; direction=false; market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
