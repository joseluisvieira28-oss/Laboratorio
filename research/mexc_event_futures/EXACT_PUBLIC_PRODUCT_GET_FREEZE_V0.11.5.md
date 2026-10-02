# MEXC EVENT FUTURES LAB — EXACT PUBLIC PRODUCT GET FREEZE V0.11.5

Date: 2026-10-02
Status: SOURCE-ONLY / PUBLIC GET / FAIL-CLOSED

## What V0.11.4 resolved

The live MEXC futures web bundle defines production:
`NEW_SWAP_API = https://www.<main-domain>/api/platform/futures/api/v1`

For `mexc.com`, the resolved base is:

`https://www.mexc.com/api/platform/futures/api/v1`

The same bundle defines Event Futures public GET functions:

- `GET /event_contract/detail` with `needLogin:false`
- `GET /event_contract/trade_date_time?symbol={symbol}` with `needLogin:false`
- `GET /event_contract/last_trade_date_time?symbol={symbol}` with `needLogin:false`
- `GET /event_contract/listPlaceCarouse`
- `GET /event_contract/listWinCarouse`

The order route is separately defined as:
`POST /private/event_contract/positions/place` with `needLogin:true`.

V0.11.5 MUST NOT call the order route or any private/account route.

## Mission

Probe only the resolved public GET endpoints above, unauthenticated, and determine whether exact current Event Futures product fields are exposed, including:

- symbols;
- enabled time units / cycles;
- payout-related fields;
- min/max amount if present;
- current trading windows;
- any settlement/product identifiers;
- any explicit index/price-source metadata.

## Hard boundary

- GET only.
- No cookies imported.
- No auth header.
- No API key.
- No account/balance/position calls.
- No private routes.
- No order placement.
- No POST/PUT/PATCH/DELETE.
- No live trading.
- No main merge.

## Verdicts

- EXACT_PRODUCT_SCHEMA_FOUND:
  public product response returns Event Futures-specific schema/data.

- EXACT_PAYOUT_FIELDS_FOUND:
  current public response contains identifiable payout fields.

- PUBLIC_ENDPOINT_FOUND_BUT_SCHEMA_INCOMPLETE:
  endpoint responds but does not expose enough exact-product fields.

- PUBLIC_ENDPOINT_BLOCKED:
  endpoint access fails.

No strategy verdict is allowed in V0.11.5.
