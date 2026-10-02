# MEXC EVENT FUTURES LAB — V0.12.1 BROWSER-BOUND EXACT GET REMEDIATION FREEZE

Date: 2026-10-02
Status: SOURCE-ONLY / PUBLIC BROWSER RESPONSE / FAIL-CLOSED

## Trigger

V0.11 anonymous Chromium observed HTTP 200 JSON from:
`https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail`

V0.12 direct requests from the GitHub runner received HTTP 403.

Therefore V0.12.1 tests only whether the exact public GET response can be captured passively from a fresh anonymous browser page load.

No trading hypothesis is tested.

## Method

- fresh Playwright Chromium context;
- zero imported cookies / no user profile;
- no login;
- abort every non-GET request;
- navigate only to the public Event Futures BTC page;
- passively capture the full response body when the exact `event_contract/detail` GET occurs;
- parse and persist the public JSON;
- print selected records for BTC_USDT, ETH_USDT, NVIDIA_USDT, MUSTOCK_USDT, SPCXSTOCK_USDT.

## Prohibited

- authentication;
- account/balance/portfolio access;
- order submission;
- private Event Contract routes;
- POST/PUT/PATCH/DELETE;
- exchange mutation;
- live trading;
- main merge.

## Verdicts

- EXACT_PUBLIC_BROWSER_ROUTE_CONFIRMED
- EXACT_ROUTE_OBSERVED_SCHEMA_INSUFFICIENT
- BROWSER_EXACT_ROUTE_NOT_CAPTURED

No edge verdict is permitted.
