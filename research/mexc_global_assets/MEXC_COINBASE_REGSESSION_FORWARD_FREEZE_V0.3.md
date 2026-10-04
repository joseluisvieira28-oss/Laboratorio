# MEXC COINBASE REGULAR-SESSION FORWARD — PRE-OUTCOME FREEZE V0.3

Date: 2026-10-04
Status: FROZEN BEFORE 2026-10-05 FORWARD OUTCOMES

## Candidate provenance

This candidate was selected after V0.2 discovery and is explicitly labeled:
`DISCOVERY_SELECTED_POST_OUTCOME_FOR_PROSPECTIVE_VALIDATION`

Selection rule:
1. Holm-selected only;
2. signals on all 17 discovery sessions;
3. mean gross >16 bps;
4. maximize mean gross minus 16 bps.

Selected cell:
- shock >=20 bps
- lag gap >=10 bps
- horizon 5 minutes
- FOLLOW_EXTERNAL_CONSENSUS
- discovery N=85
- wins=65
- win rate=76.4706%
- mean gross=+18.979356 bps
- median gross=+17.936214 bps
- thirds=+14.968761 / +19.530940 / +22.319089 bps
- p=5.149437e-7
- signals on 17/17 sessions

## Prospective window

Use every weekday session:
`2026-10-05 ... 2026-10-30`

20 fixed sessions.

Signal window:
`14:31 ... 18:44 UTC`

No interim promotion.
Evaluate only after the full window ends.

## Frozen signal

External return:
`mean(Binance COINUSDT 1m return, Bitget COINUSDT 1m return)`

MEXC return:
`COINBASE_USDT 1m return`

Lag gap:
`external_return - mexc_return`

Signal requires:
- abs(external return) >=20 bps
- sign(lag gap) == sign(external return)
- abs(lag gap) >=10 bps

Direction:
`FOLLOW_EXTERNAL_CONSENSUS`

Outcome horizon:
`5 minutes`

Cooldown:
`5 minutes`

Exact observable-minute alignment only.
No forward fill or interpolation.

## Scientific PASS

Requires all:
- N >=60
- signals on >=15 distinct sessions
- mean gross >0
- median gross >0
- win rate >50%
- both chronological half means >0
- exact one-sided binomial p <0.05

## Execution screen — descriptive only

Public standard MEXC API fee references:
- maker-maker round trip: 12 bps
- taker-taker round trip: 16 bps

Report:
- fee-only survival if mean gross >16 bps
- conservative fee+2bps reserve if mean gross >18 bps

This is NOT execution validation.

It excludes spread, slippage, latency, adverse selection, funding and fill probability.

## No rescue

Do not change thresholds, horizon, direction, session window, sources, cooldown or gates after forward outcomes begin.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
