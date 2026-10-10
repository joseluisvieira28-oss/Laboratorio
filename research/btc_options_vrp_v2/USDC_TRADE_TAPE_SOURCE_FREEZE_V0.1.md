# BTC-OPTIONS-VRP-001 V2 — BTC_USDC PUBLIC TRADE-TAPE SOURCE FEASIBILITY FREEZE V0.1
Date: 2026-10-07
Status: SOURCE-ONLY / NO PRICES RETAINED / NO PNL

## Question
Does the public unauthenticated Deribit historical trade tape for BTC_USDC linear options provide materially usable execution-source density at the 0.01-contract minimum size?

This is NOT a strategy backtest and cannot adjudicate edge.

## Source
history.deribit.com/api/v2/public:
- get_last_trades_by_currency_and_time
- currency=USDC
- kind=option
- bounded UTC windows only

No authentication.
No account.
No orders.
No wallet.

## Frozen probe windows
Recent pre-probe Thursdays, 06:00–10:00 UTC:
- 2026-09-03
- 2026-09-10
- 2026-09-17
- 2026-09-24
- 2026-10-01
- 2026-10-07

For 2026-10-07, end is capped at probe execution time if earlier than 10:00 UTC; because execution occurs after 10:00 UTC, full window is allowed.

## Retained fields
Only:
- timestamp;
- instrument_name;
- direction;
- amount;
- trade_id;
- block-trade flag if present.

Explicitly DO NOT retain/print:
- trade price;
- mark price;
- index price;
- IV;
- strategy return;
- PnL;
- future outcomes.

## Descriptive outputs
Per window:
- BTC_USDC option trade count;
- unique instruments;
- BUY/SELL counts;
- amount >=0.01 count;
- amount distribution summary;
- required-field coverage.

Aggregate source classification:
- SOURCE_ROUTE_PRESENT if all six windows return at least one BTC_USDC option trade and required-field coverage >=95%;
- SOURCE_ROUTE_SPARSE if source is valid but one or more windows are empty;
- SOURCE_BLOCKED only for transport/auth/provenance failure.

SOURCE_ROUTE_PRESENT is source feasibility only, not execution PASS.
