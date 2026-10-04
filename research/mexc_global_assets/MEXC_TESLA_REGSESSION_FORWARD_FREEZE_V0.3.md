# MEXC TESLA REGULAR-SESSION FORWARD VALIDATION — PRE-OUTCOME FREEZE V0.3

Date: 2026-10-04
Status: FROZEN BEFORE 2026-10-05 FORWARD OUTCOMES

## Prior authority

TESLA V0.2 copied exactly the sole NVIDIA V0.5 Holm survivor before opening TESLA outcomes.

Transferred frozen cell:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon = 1 minute
- direction = FOLLOW_EXTERNAL_CONSENSUS

TESLA replication result:
- N=222
- wins=148
- win rate=66.6667%
- mean gross=+3.330474 bps
- median gross=+3.010349 bps
- exact p=3.836663e-7
- chronological thirds=+3.478851 / +2.370311 / +4.142260 bps

Classification:
`CROSS_ASSET_REPLICATION_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

## Prospective forward window

Use every weekday session from:
`2026-10-05 ... 2026-10-30`

Expected sessions:
`20`

Signal window:
`14:31 ... 18:44 UTC`

October 2026 remains on U.S. daylight-saving time throughout the frozen window.

## Exact frozen signal

External return:
`mean(Binance TSLAUSDT 1m return, Bitget TSLAUSDT 1m return)`

MEXC return:
`TESLA_USDT 1m return`

Lag gap:
`external_return - MEXC_return`

Signal requires:
- abs(external return) >= 5 bps
- sign(lag gap) == sign(external return)
- abs(lag gap) >= 3 bps

Direction:
`FOLLOW_EXTERNAL_CONSENSUS`

Horizon:
`1 minute`

Cooldown:
`1 minute`

Exact observable-minute alignment only.
No forward fill or interpolation.

## Forward PASS gate

PASS requires all:
- N >= 100
- signals on at least 15 distinct sessions
- mean gross signed return > 0
- median gross signed return > 0
- win rate > 50%
- first chronological half mean > 0
- second chronological half mean > 0
- exact one-sided binomial p < 0.05

Only one frozen cell is evaluated, so no multiplicity correction is required.

If sample coverage is insufficient:
`TESLA_FORWARD_UNDERPOWERED`

If adequately powered but gates fail:
`TESLA_FORWARD_VALIDATION_FAIL`

If all gates pass:
`TESLA_FORWARD_VALIDATED_REPLICATION__EXECUTION_FEASIBILITY_SEPARATE`

## Costs

Report round-trip scenarios:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Costs remain separate from scientific validation.

## No peeking / no rescue

Do not evaluate for promotion before the complete frozen window ends.

Do not change:
- thresholds
- horizon
- direction
- external legs
- signal window
- cooldown
- N/session gates
- statistical gate
- sample dates

No private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
