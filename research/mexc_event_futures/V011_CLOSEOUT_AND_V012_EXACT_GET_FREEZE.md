# MEXC EVENT FUTURES LAB — V0.11 CLOSEOUT + V0.12 EXACT PUBLIC GET FREEZE

Date: 2026-10-02
Status: SOURCE-ONLY / PUBLIC GET / FAIL-CLOSED

## V0.11 finding

A fresh anonymous Chromium session loaded the exact Event Futures BTC page and visibly showed:
- BTCUSDT;
- current index/market values;
- Up Payout 80%;
- Down Payout 80%.

The browser also observed a successful public GET response from:

`https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail`

with Event Futures-specific JSON beginning with a BTC_USDT contract record.

No login, account request, order, or mutation occurred.

## V0.12 objective

Probe only the discovered public Event Futures GET route and document its exact response schema and current product values for:
BTC_USDT, ETH_USDT, NVIDIA_USDT, MUSTOCK_USDT, SPCXSTOCK_USDT.

V0.12 is SOURCE-ONLY. No trading hypothesis or historical profitability test is permitted.

## Allowed

- unauthenticated GET to the exact discovered Event Futures detail route;
- record HTTP status, headers, SHA256, schema keys and selected contract records;
- identify payout fields, supported cycles/time units, limits, status flags and settlement/index metadata if present;
- compare the public response to the anonymous visible page values.

## Prohibited

- authentication;
- cookies from a user session;
- private endpoints;
- orders;
- exchange/account mutation;
- POST/PUT/PATCH/DELETE;
- live trading;
- main merge.

## Verdicts

- EXACT_PUBLIC_PRODUCT_ROUTE_CONFIRMED
- PUBLIC_ROUTE_FOUND_BUT_SCHEMA_INSUFFICIENT
- PUBLIC_ROUTE_BLOCKED

No edge verdict is allowed.
