# DEFI-LIQUIDATION-SHOCK-001 — CONVEXITY SOURCE FEASIBILITY CLOSEOUT V0.1

Date: 2026-09-29
Branch: dls-convexity-source-gate-v01
Family ID: DLS-CONVEXITY-001

## Terminal classification

DLS_CONVEXITY_SOURCE_BLOCKED

This classification applies to a FREE/PUBLIC, historically executable SOL options test under the
pre-frozen source requirements.

No option price, return or PnL outcome was opened.

## Freeze authority

DLS_CONVEXITY_SOURCE_FEASIBILITY_FREEZE_V0.1.md

Freeze commit:
c22118cb358eb6b614b504069d0e4847c33d916e

## Instrument-history feasibility

Deribit source:
https://insights.deribit.com/education/new-altcoin-options-on-deribit-sol-xrp-matic/

Source states that SOL/XRP/MATIC options launched in March 2024.

Binance source:
https://www.binance.com/en/square/post/15908692098801

Source states that Binance launched SOLUSDT daily/weekly options on 2024-11-12 08:00 UTC.

Therefore the preferred existing DLS development history 2021-12-08 through 2023-12-31 cannot support
an executable SOL-options strategy because the relevant SOL option markets did not yet exist.

## 2024 alternative feasibility

A 2024-only source path was assessed because Deribit SOL options existed from March 2024.

Current Deribit API documentation index:
https://docs.deribit.com/llms.txt

The public API exposes:
- historical trades by currency/instrument and time;
- historical 5-minute mark price data;
- current order book/best bid/ask retrieval;
- historical instrument metadata.

The documentation index does not expose a public historical order-book/top-of-book-by-time endpoint.

Historical trade prints do not satisfy the frozen executable evidence requirement because they do not
prove the contemporaneous bid/ask spread or executable price for the strategy at the required timestamp.

Mark-price history is also insufficient for executable entry/exit.

## Paid historical quote source

Tardis:
https://tardis.dev/

Tardis advertises historical:
- options chain data;
- top-of-book/quotes;
- L2 order books;
- trades;
including Deribit and other options venues.

Current access is commercial/paid.

Under the Crypto Lab policy to prioritize public/free sources, this route is not opened.

## Why this is BLOCKED, not NO_EDGE

No options economic outcome was tested.

The block is source/execution provenance:
- no SOL option market during the existing 2021-2023 development period;
- 2024 has option instruments, but the free/public source set identified here does not provide the
  contemporaneous historical bid/ask evidence required by the freeze for a defensible executable test.

Therefore the convexity hypothesis remains scientifically UNTESTED.

## Reopen condition

This family may be reopened only if a future FREE/PUBLIC source can provide:
- historical SOL option instrument metadata;
- timestamped executable bid/ask/top-of-book across a prospectively frozen 2024 interval;
- sufficient independent development/OOS coverage before protected 2025/2026;
- reproducible source provenance.

A paid dataset would require explicit operator authorization because it changes the cost/data policy.

## Firewall

option_prices_opened=false
option_returns_opened=false
option_pnl_opened=false
market_2025_opened=false
market_2026_opened=false
paid_source=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
