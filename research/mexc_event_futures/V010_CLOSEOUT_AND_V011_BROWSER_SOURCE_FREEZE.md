# MEXC EVENT FUTURES LAB — V0.10 CLOSEOUT + V0.11 BROWSER SOURCE FREEZE

Date: 2026-10-02
Status: SOURCE-ONLY / PUBLIC BROWSER / FAIL-CLOSED

## V0.10 closeout

V0.10 tested peer-breadth consensus across the five displayed Event Futures underlyings.

Result:
- frozen discovery cells: 320
- basic discovery-eligible cells: 0
- BH-selected: 0
- August OOS opened: 0
- September holdout: LOCKED / NOT FETCHED

Verdict:
**NO_PROXY_SURVIVOR for the frozen peer-breadth family.**

## Why V0.11

The earlier requests-based public-web source probe was blocked by bot/static-asset access from GitHub Actions.

V0.11 attacks the exact-product source problem with a real browser engine while preserving a strict no-auth/no-order boundary.

No trading hypothesis is tested in V0.11.

## Entry page

Primary:
`https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT`

Fallback:
`https://www.mexc.com/en-US/futures/prediction-futures/BTC_USDT`

## Browser boundary

Use a fresh Playwright Chromium context.

Must:
- start with zero cookies;
- never log in;
- never import a user/browser profile;
- never set API keys or auth headers;
- never click Up/Down;
- never click submit/order buttons;
- never visit account/balance/portfolio pages;
- never persist user identifiers.

Network handling:
- GET requests may proceed.
- Any non-GET browser request MUST be aborted and logged by method + URL only.
- This means if the product uses POST/GraphQL for data, V0.11 will identify the attempted route but will not transmit it.

## Evidence to collect

1. navigation status/title/final URL;
2. public visible body-text snippets around:
   - payout
   - 80%
   - time unit
   - 10 minutes / 30 minutes / 1 hour / 1 day
   - BTCUSDT / BTC_USDT
   - Up / Down
3. all network GET URLs matching likely product/data terms;
4. JSON/text response previews for public GET responses that mention:
   - payout
   - prediction
   - event future
   - timeUnit
   - BTC_USDT
5. loaded JavaScript asset URLs and SHA256;
6. bounded keyword/route extraction from loaded JavaScript;
7. all aborted non-GET request URLs/methods;
8. explicit counters:
   authenticated_requests = 0
   orders = 0
   account_mutations = 0

## Bounds

- page timeout: 60s
- settle/wait after DOM load: <= 25s
- maximum 120 network records
- maximum 60 JS assets inspected
- maximum 8 MiB per JS asset
- maximum 80 response previews
- no recursive crawling beyond directly loaded page assets

## Verdicts

- `EXACT_PUBLIC_GET_ROUTE_FOUND`:
  public GET response visibly contains Event Futures-specific payout/time-unit/product data.

- `VISIBLE_EXACT_PRODUCT_DATA_FOUND_NO_ROUTE`:
  page visibly exposes payout/time-unit data but the exact backing public GET route is not isolated.

- `CANDIDATE_ROUTE_IDENTIFIED_BUT_BLOCKED`:
  candidate route or non-GET data method is observed but intentionally not transmitted / not proven.

- `BROWSER_SOURCE_BLOCKED`:
  browser challenge/region/access prevents usable page data.

- `NO_EXACT_PRODUCT_SOURCE_FOUND`:
  page loads normally but no defensible exact-product source is identified.

## Hard boundaries

- No authenticated requests.
- No cookies from a real account.
- No order placement.
- No exchange mutation.
- No live trading.
- No main merge.
