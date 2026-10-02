# MEXC EVENT FUTURES LAB — OPTIONS SIGNAL TRANSFER V0.8B — BINANCE SPOT PROXY FREEZE

Date: 2026-10-02
Status: PRE-OUTCOME / SOURCE-TRANSFER-ONLY / FAIL-CLOSED

## Why V0.8B is allowed

V0.8 attempted the already-frozen OPTIONS-SPOTPERP signal transfer using historical MEXC standard-futures BTC index Min5 data.

V0.8 source result:
- requested historical coverage: 2021-04 through 2025-12;
- public MEXC Min5 index route returned data only from approximately 2025-10-06 onward;
- all 2021-2024 parent Discovery signal events were therefore unresolved;
- discovery coverage: 0%;
- no V0.8 directional accuracy, p-value, EV, BH selection, or OOS outcome was computed.

Verdict:
`SOURCE_BLOCKED_MEXC_INDEX_HISTORY`.

Because no V0.8 outcomes were observed, a pre-outcome source transfer is permitted without scientific rescue.

## V0.8B question

Does the immutable OPTIONS-SPOTPERP-001 parent signal predict short-horizon BTC direction in a second, historically complete public spot-price proxy?

V0.8B is NOT an exact MEXC Event Futures backtest.
It is a signal-transfer feasibility test.

## Immutable parent signal

Unchanged from V0.8:

`OPTIONS-SPOTPERP-001 / V2.1`

- positive CALL_IV_MINUS_PUT_IV -> UP
- negative CALL_IV_MINUS_PUT_IV -> DOWN
- zero -> no signal
- entry clock = 00:00 UTC on signal date t+1

Parent artifacts remain immutable:

Discovery:
- run `34858777691`
- artifact `10354131731`
- expected ledger rows: 1210
- signal period: 2021-04 through 2024-12

Independent parent OOS:
- run `35231711508`
- artifact `10504812106`
- expected ledger rows: 363
- signal period: calendar 2025

No 2026 signal data are used.

## Frozen alternative outcome source

Binance public historical archive:

`https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/5m/BTCUSDT-5m-YYYY-MM.zip`

Required months:
2021-04 through 2025-12 only.

Price used at an Event Futures clock timestamp:
the **open price of the Binance 5-minute bar whose open timestamp equals that exact UTC timestamp**.

No nearest-bar substitution.
No interpolation.
No close-price substitution after outcomes.
No alternate exchange after outcomes.

Timestamp normalization:
- accept documented historical millisecond timestamps;
- if a source row is in microseconds, divide by 1000 exactly;
- any other magnitude => fail closed.

## Frozen Event Futures horizons

- 10m
- 30m
- 60m
- 1440m

Entry:
00:00 UTC at t+1.

Prediction:
parent sign.

Outcome:
sign(Binance_5m_open[t+1+H] - Binance_5m_open[t+1]).

Tie:
excluded from binomial N.

## Discovery / OOS gates

Identical to V0.8.

Discovery:
2021-2024 parent Discovery ledger.

Per horizon:
- source coverage >=95%;
- non-tie N >=500;
- accuracy >55.5555556%;
- Wilson 95% lower bound >50%;
- at least 3 of 4 years accuracy >50%;
- exact one-sided binomial p vs p0=55.5555556%.

Benjamini-Hochberg FDR q=0.05 across the four horizons.

Only BH-selected horizons open 2025 parent OOS.

2025 OOS:
- source coverage >=95%;
- non-tie N >=250;
- accuracy >55.5555556%;
- Wilson 95% lower bound >50%;
- exact one-sided p <0.05;
- illustrative EV at 80% payout >0;
- at least 3 of 4 quarters accuracy >50%.

## Classification

If no Discovery horizon survives:
`NO_PROXY_SURVIVOR_AT_FROZEN_V08B_GATE`.

If a selected horizon passes 2025 OOS:
`CROSS_SOURCE_PROXY_CANDIDATE__OPTIONS_SIGNAL_TRANSFER`.

Even a survivor remains NOT exact Event Futures evidence.

## Hard boundaries

- no 2026 data;
- no live trading;
- no MEXC account calls;
- no Event Futures orders;
- no parent rule changes;
- no horizon rescue;
- no post-outcome source change;
- no merge to main.
