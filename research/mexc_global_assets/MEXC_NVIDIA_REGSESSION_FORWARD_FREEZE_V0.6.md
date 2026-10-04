# MEXC NVIDIA REGULAR-SESSION FORWARD VALIDATION — PRE-OUTCOME FREEZE V0.6

Date: 2026-10-04
Status: FROZEN BEFORE 2026-10-05 FORWARD OUTCOMES

## Discovery authority

V0.5 produced exactly one Holm-selected cell from 64 frozen cells:

- shock threshold: 5 bps
- lag-gap threshold: 3 bps
- horizon: 1 minute
- direction: FOLLOW_EXTERNAL_CONSENSUS
- N=92
- wins=64
- win rate=69.5652%
- mean gross=+3.758750 bps
- median gross=+4.297843 bps
- exact p=0.0001112506
- Holm cutoff=0.00078125
- chronological thirds=+3.817834 / +4.254712 / +3.205612 bps

V0.6 validates only this exact cell.

## Prospective window

Use all weekday sessions from:

`2026-10-05 ... 2026-10-30`

20 fixed sessions.

The forward study must not be evaluated for promotion before the complete window ends.

Signal window remains:

`14:31 ... 18:44 UTC`

October 2026 remains on U.S. daylight-saving time throughout this fixed window, so no clock conversion is needed.

## Frozen signal

External return:
`mean(Binance NVDAUSDT 1m return, Bitget NVDAUSDT 1m return)`

MEXC return:
`NVIDIA_USDT 1m return`

Lag gap:
`external_return - MEXC_return`

Signal requires all:
- abs(external return) >= 5 bps
- sign(lag gap) == sign(external return)
- abs(lag gap) >= 3 bps

Direction:
`FOLLOW_EXTERNAL_CONSENSUS`

Outcome horizon:
`1 minute`

Cooldown:
`1 minute`

Exact observable-minute alignment only.
No forward fill or interpolation.

## Validation gate

PASS requires all:
- N >= 50
- signals on at least 15 distinct sessions
- mean gross signed return > 0
- median gross signed return > 0
- win rate > 50%
- first chronological half mean > 0
- second chronological half mean > 0
- exact one-sided binomial p < 0.05

There is one frozen cell, so no multiplicity correction is required.

If the sample is too small, classify `FORWARD_UNDERPOWERED`, not failure.

## Costs

Report round-trip scenarios:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Execution cost is not a scientific validation gate.
Execution feasibility is evaluated separately.

## No peeking / no rescue

No interim promotion is authorized.

Do not:
- alter thresholds;
- alter horizon;
- alter direction;
- alter session window;
- change Binance/Bitget consensus;
- select favorable days;
- lower N or session coverage gates;
- tune after seeing forward outcomes.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
