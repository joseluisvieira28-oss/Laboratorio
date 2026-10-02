# MEXC EVENT FUTURES LAB — V0.13 PUBLIC ROUTE MAP FREEZE

Date: 2026-10-02
Status: SOURCE-ONLY / PUBLIC BROWSER / FAIL-CLOSED

## Known exact source

V0.12.1 passively captured HTTP 200 public JSON from:
`/api/platform/futures/api/v1/event_contract/detail`

It confirmed 9 currently exposed Event Futures symbols and horizon-specific payout configuration.

## Objective

Map all Event Futures-specific public route strings and public GET responses loaded by the anonymous Event Futures page, with priority on:
- exact index/settlement price;
- cycle/time-unit state;
- product ticker/market data;
- public Event Futures history if any;
- current payout source.

## Method

Fresh anonymous Chromium. Abort every non-GET request. No login/cookies/user profile.
Inspect directly loaded JS assets and all public GET responses for strings containing:
`event_contract`, `eventContract`, `prediction-futures`, `event-futures`.

Persist route strings and snippets only.

## Prohibited

Authentication, private endpoints, order submission, account mutation, live trading, main merge.

No edge verdict is permitted.
