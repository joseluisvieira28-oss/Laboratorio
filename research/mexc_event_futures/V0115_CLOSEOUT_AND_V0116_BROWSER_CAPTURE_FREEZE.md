# MEXC EVENT FUTURES LAB — V0.11.5 CLOSEOUT + V0.11.6 BROWSER EXACT-PRODUCT CAPTURE FREEZE

Date: 2026-10-03
Status: SOURCE-ONLY / FAIL-CLOSED / NO AUTH / NO ORDERS

## V0.11.5 correction

V0.11.5 resolved the production base used by the live web bundle as:

`https://www.mexc.com/api/platform/futures/api/v1`

The V0.11.5 GitHub Actions run issued 13 unauthenticated GET requests to the resolved Event Futures paths. Every response was HTTP 403 `text/html`. No Event Futures JSON schema and no payout fields were observed.

Therefore the correct closeout is:

`PUBLIC_ENDPOINT_PATH_RESOLVED_BUT_ACCESS_BLOCKED_FROM_RUNNER`

The previous label `PUBLIC_ENDPOINT_FOUND_BUT_SCHEMA_INCOMPLETE` is superseded because no product schema was received.

The live bundle mapping also requires this correction:

- `GET /event_contract/detail` => `needLogin:true`
- `GET /event_contract/trade_date_time?symbol={symbol}` => `needLogin:false`
- `GET /event_contract/last_trade_date_time?symbol={symbol}` => `needLogin:false`
- `POST /private/event_contract/positions/place` => authenticated private order route; prohibited.

## V0.11.6 mission

Use a fresh, unauthenticated Chromium context to observe the normal public Event Futures page and determine whether browser session state is sufficient to expose any exact-product read-only traffic or schema that direct runner GETs could not access.

Target page:

`https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT`

V0.11.6 may:

1. passively capture browser-generated GET requests/responses whose URLs contain Event Futures / `event_contract` / relevant public websocket traffic;
2. actively issue same-origin browser `fetch` GETs only to the two bundle-proven public routes:
   - `/event_contract/trade_date_time?symbol=...`
   - `/event_contract/last_trade_date_time?symbol=...`;
3. inspect public JS bundles for exact field names and mapping around Event Futures, payout, cycle, time unit, settlement/index and websocket topics;
4. save bounded, sanitized evidence with hashes.

## Hard boundary

- Fresh browser context; no imported profile or cookies.
- No login.
- No API key.
- No Authorization header.
- No private/account/balance/position/order endpoints.
- No active request to `/event_contract/detail` because the bundle marks it `needLogin:true`.
- Browser-generated GET to `/event_contract/detail` may be observed passively only.
- Abort every POST/PUT/PATCH/DELETE before transmission.
- Abort sensitive GETs containing `/private/`, account, balance, position, wallet, order or user routes.
- No order placement.
- No live trading.
- No wallet action.
- No exchange mutation.
- No main merge.
- No historical holdout opening.

## Symbols for public schedule probe

- BTC_USDT
- ETH_USDT
- NVIDIA_USDT
- MUSTOCK_USDT
- SPCXSTOCK_USDT

## Evidence sought

- actual Event Futures request URLs and HTTP statuses from a browser session;
- JSON schema for public schedule/time endpoints, if obtainable;
- any public current product schema reached passively;
- identifiable payout field names or values;
- cycle/time-unit/min-max/price/index/settlement identifiers if exposed;
- public websocket URL/topic and received product messages if the normal page opens them;
- static JS property names/functions consuming Event Futures data.

Sensitive keys such as token, secret, password, cookie, authorization and API key must be redacted from saved JSON.

## Verdict hierarchy

1. `EXACT_PAYOUT_FIELDS_FOUND`
   - exact public/read-only browser response contains identifiable payout fields.

2. `EXACT_PRODUCT_SCHEMA_FOUND`
   - an Event Futures-specific public/read-only response exposes product schema but payout remains unresolved.

3. `PUBLIC_SCHEDULE_SCHEMA_FOUND_PAYOUT_UNRESOLVED`
   - proven public time/schedule endpoints return JSON but product/payout source remains unresolved.

4. `STATIC_PRODUCT_MAPPING_FOUND_RUNTIME_SOURCE_BLOCKED`
   - bundle mapping advances field/source knowledge but runtime product data remains inaccessible.

5. `BROWSER_EVENT_CONTRACT_ACCESS_BLOCKED`
   - browser Event Futures traffic is observed but access is blocked and no usable schema is received.

6. `SOURCE_BLOCKED`
   - no defensible exact-product runtime source or useful static mapping is found.

No trading-edge verdict is allowed in V0.11.6.
