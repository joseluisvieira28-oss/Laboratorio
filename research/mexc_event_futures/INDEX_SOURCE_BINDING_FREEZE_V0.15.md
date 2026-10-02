# MEXC EVENT FUTURES LAB — INDEX SOURCE BINDING FREEZE V0.15

Date: 2026-10-02
Status: SOURCE-ONLY / PUBLIC BROWSER / FAIL-CLOSED

## Objective

Determine which public futures market-data GET routes are actually loaded by the anonymous Event Futures BTC page, with emphasis on the index price used by the displayed product.

## Method

Fresh anonymous Chromium loads:
`https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT`

Capture only GET responses whose URL is under:
`/api/platform/futures/api/v1/`

Persist:
- URL/status/content type;
- JSON top-level keys;
- BTC_USDT record or object when present;
- endpoints containing ticker, index, kline, event_contract.

Abort all non-GET browser requests.

## Goal

Establish a defensible source-binding statement between the Event Futures page and the public futures market-data/index source.

## Prohibited

Authentication, user cookies, private endpoints, orders, account mutation, live trading, main merge.

No edge/profitability verdict is permitted.
