# MEXC EVENT FUTURES LAB — EXACT PRODUCT SOURCE DISCOVERY V0.6

Date: 2026-10-02
Status: SOURCE-ONLY / PUBLIC WEB ASSETS / FAIL-CLOSED
Branch: `mexc-event-futures-exact-source-v0.6-2026-10-02`

## Mission

Identify the public, unauthenticated web-data routes used by the MEXC Event Futures page for:

- supported Event Futures instruments;
- current Up payout;
- current Down payout;
- available expiry / time units;
- displayed Event Futures index price;
- product-specific trading limits / price limits if exposed publicly;
- settlement-relevant product metadata.

This phase MUST NOT test a trading hypothesis and MUST NOT calculate strategy outcomes.

## Authority boundary

Allowed:
- GET public MEXC web pages;
- GET public JavaScript/static assets referenced by those pages;
- inspect strings, route fragments, GraphQL operation names, REST paths, websocket topics, hostnames, parameter names, and response schemas;
- probe only candidate public GET endpoints discovered from the page/assets or official documentation;
- persist source receipts and evidence;
- create follow-on source-only workflows.

Prohibited:
- login;
- cookies copied from an authenticated session;
- private/authenticated API calls;
- POST/PUT/PATCH/DELETE to MEXC;
- order submission;
- balance/portfolio/account calls;
- browser automation that clicks Up/Down;
- exchange mutation;
- live trading;
- merging to main.

## Bounded asset inspection

Entry page:
`https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT`

Legacy alias may also be inspected:
`https://www.mexc.com/en-US/futures/prediction-futures/BTC_USDT`

Static asset discovery is bounded:
- maximum 80 script/style assets fetched;
- maximum 8 MiB per asset;
- same MEXC/Mocortech static hosts only;
- no recursive crawling beyond assets directly referenced by the entry page unless a directly referenced JS chunk names another chunk manifest.

Search terms include:
`event-futures`, `prediction-futures`, `payout`, `timeUnit`, `8938`,
`upPayout`, `downPayout`, `settlement`, `prediction`, `eventFuture`,
`/api/`, `wss://`, and likely product-specific route names.

## Source verdicts

- `EXACT_PUBLIC_ROUTE_FOUND`: at least one public route returns Event Futures-specific current product data including payout/time-unit or equivalent.
- `CANDIDATE_ROUTE_FOUND_UNPROVEN`: route fragments are found but public probing does not yet establish product data.
- `PUBLIC_WEB_ROUTE_NOT_IDENTIFIED`: bounded asset inspection yields no defensible route.
- `BLOCKED_BY_BOT_OR_ASSET_ACCESS`: page/static access prevents inspection.

No scientific edge verdict is allowed in V0.6.

## Evidence requirements

Persist:
1. page fetch receipt;
2. referenced asset inventory;
3. matched snippets with source asset URL and SHA256;
4. extracted candidate routes/hosts/operation names;
5. public GET probe results;
6. final source verdict;
7. explicit statement that no authenticated request or order occurred.
