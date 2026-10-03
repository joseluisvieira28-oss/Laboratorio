# OPTIONS-RR-TERM-FWD-001 — PUBLIC SOURCE GATE FREEZE V0.1

Date: 2026-10-03
Status: PRE-OUTCOME / SOURCE-ONLY / FORWARD-ONLY
Parent protocol: EVENT_CONDITIONED_EDGE_FREEZE_V0.13.md

## Economic hypothesis

This family tests the **term structure of 25-delta risk-reversal skew** rather than:
- the absolute near-expiry skew level used by OPTIONS-VOL-FWD-001;
- the day-to-day ETH skew change used by OPTIONS-ETH-SKEW-SHOCK-001;
- DVOL futures term structure.

For each currency:

`rr_skew_pp(expiry) = put_mark_iv_25d - call_mark_iv_25d`

`rr_term_pp = rr_skew_pp(short) - rr_skew_pp(medium)`

Interpretation fixed before outcomes:
- positive rr_term_pp = near-term downside insurance richer than medium-term downside insurance;
- negative rr_term_pp = near-term downside insurance cheaper / relatively more upside-skewed than medium term.

No price outcome is used in source selection or calibration.

## Public source

Deribit public unauthenticated API only:
- get_instruments
- get_book_summary_by_currency
- ticker

Currencies:
- BTC
- ETH

No login, API key, private endpoint, account read or order.

## Frozen expiry buckets

At each source round and currency:

SHORT:
- active option expiry with DTE in [7,21] calendar days;
- choose nearest eligible expiry.

MEDIUM:
- active option expiry with DTE in [35,70] calendar days;
- choose nearest eligible expiry.

SHORT and MEDIUM must be distinct expiries.
No fallback outside the bucket.

## Frozen 25-delta selection

For each selected expiry independently:

- calls and puts must be active options for the same currency/expiry;
- candidate call must be OTM: strike > underlying;
- candidate put must be OTM: strike < underlying;
- preselection uses public mark IV/underlying only to identify the closest approximate 25-delta candidates;
- fetch ticker for up to the two closest call and two closest put candidates;
- exact accepted call delta must be in [+0.15,+0.35];
- exact accepted put delta must be in [-0.35,-0.15];
- choose the valid ticker with minimum | |delta| - 0.25 |, tie by instrument name.

Accepted ticker must preserve the existing V0.13 validity rules:
- state=open;
- fresh timestamp;
- finite positive mark_iv, bid_iv, ask_iv, index_price, underlying_price,
  best bid/ask price and amount;
- ask >= bid for price and IV.

Within-expiry call/put source timestamp spread:
<= 5000 ms.

Cross-expiry source timestamp spread across the four selected tickers:
<= 10000 ms.

## Source gate

One source-gate run performs 3 independent rounds.

PASS requires:
- all 3 BTC rounds have valid SHORT and MEDIUM 25-delta pairs;
- all 3 ETH rounds have valid SHORT and MEDIUM 25-delta pairs;
- all expiry/bucket rules satisfied;
- all timestamp-spread rules satisfied;
- no source exceptions.

The source gate records rr_skew_pp(short), rr_skew_pp(medium), and rr_term_pp only as
source feasibility observations.

It opens zero price outcomes and zero Event Futures outcomes.

Verdicts:
- SOURCE_GATE_PASS
- PARTIAL_SOURCE
- SOURCE_BLOCKED

## Future direction rule — frozen concept, numeric threshold not yet known

If a later source-only calibration legitimately passes:

- rr_term_pp >= +threshold(symbol) => DOWN
- rr_term_pp <= -threshold(symbol) => UP
- otherwise NO_SIGNAL

This is `FOLLOW_NEAR_TERM_DOWNSIDE_STRESS`.

Exact threshold MUST come only from a separately frozen forward source-only calibration.
No historical outcome optimization is authorized.

Proposed Event Futures horizon after future activation:
10 minutes.

## Governance

- no MEXC data in source gate;
- no price future/outcome;
- no threshold tuning from returns;
- no rescue of OPTIONS-VOL V0.1/V0.2 or ETH skew-shock;
- no 2026 backfill;
- no live trading;
- no orders;
- no private/account/wallet endpoints;
- no merge to main.
