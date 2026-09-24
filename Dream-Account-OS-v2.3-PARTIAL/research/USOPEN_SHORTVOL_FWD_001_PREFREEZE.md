# USOPEN-SHORTVOL-FWD-001 — U.S. OPEN SHORT-VOL FORWARD SHADOW — PRE-FREEZE

Date frozen: 2026-09-24
Status: PRE_FORWARD_FROZEN
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Research only: TRUE
Live execution: FALSE
Orders: FALSE

## Why this is a new lab

USOPEN-STRADDLE-001 retrospectively found that buying a 7–14 DTE ATM BTC straddle at 09:00 ET and selling it at 11:00 ET was strongly negative on 2024H1 price-only data. That block is contaminated and may not be inverted for scientific credit.

This lab therefore tests the opposite economic hypothesis **only prospectively from the freeze boundary forward** using live public Deribit BBO snapshots with displayed sizes. No pre-freeze 2026 outcomes may be backfilled.

## Frozen shadow rule

Universe:
- Deribit BTC options only.

Clock:
- America/New_York, DST-aware;
- regular U.S. cash-market weekdays only.

Entry:
- first valid source capture in 09:00–09:10 ET;
- current BTC index price from public index endpoint;
- choose nearest expiry with 7 <= DTE <= 14;
- choose same-strike call+put nearest to current BTC index;
- require positive non-crossed bid/ask and displayed bid/ask amount >= 0.1 BTC option amount on both legs;
- shadow SELL 0.1 BTC call at bid and SELL 0.1 BTC put at bid.

Exit:
- first valid source capture in 11:00–11:10 ET;
- exact same call and put;
- require positive non-crossed bid/ask and displayed ask amount >= 0.1 on both legs;
- shadow BUY BACK both legs at ask.

Missing quote/size => date is SOURCE_INELIGIBLE. Never widen windows after outcomes.

## Costs

Historical/current standard-account research model:
- 0.0003 BTC fee per 1 BTC option amount per trade side;
- scaled to 0.1 BTC option amount;
- capped at 12.5% of option premium per trade;
- no delivery fee; positions close intraday.

Base PnL uses bid sale -> ask buyback plus fees.

Stress PnL subtracts one additional adverse spread per leg, defined as max(entry spread, exit spread) × 0.1.

## Forward gate

No adjudication before at least 30 completed eligible dates.

At 30+ completed dates, candidate survives forward shadow only if all are true:
- mean base net BTC > 0;
- base PF >= 1.20;
- date-bootstrap lower 95% of mean base net BTC > 0;
- mean stress net BTC > 0;
- stress PF > 1;
- at least 2 calendar months have nonnegative mean base net;
- maximum single positive episode share <= 25%.

Passing classification:
`FORWARD_SHADOW_SHORTVOL_SURVIVES`

Failing classification:
`FORWARD_SHADOW_SHORTVOL_NO_EDGE`

Until N>=30:
`FORWARD_SHADOW_COLLECTING`

## Risk / interpretation

Short straddles have asymmetric tail risk. Even a statistical pass does not authorize capital.
Always report worst episode, max drawdown and positive-tail concentration.

## Firewall

Forbidden:
- historical backfill before 2026-09-24 freeze boundary;
- using 2024H1 long-straddle outcomes as short-straddle validation;
- timestamp/DTE/strike tuning;
- midpoint fills;
- ignoring displayed size;
- changing amount after outcomes;
- live orders;
- authenticated/private endpoints;
- wallet access;
- exchange mutation;
- merge to main.
