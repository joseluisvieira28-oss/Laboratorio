# MEXC MSTR REGULAR-SESSION PACK — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE MSTR OUTCOMES

## Source authority

Target:
- MEXC `MSTRSTOCK_USDT`

External public legs:
- Binance Futures `MSTRUSDT`
- Bitget Futures `MSTRUSDT`

MEXC declared index origins:
- BINANCE_FUTURE
- BITGET_FUTURE
- BINANCETICKER
- PYTH
- KAIKO

Source gate:
- run `37229992553`
- verdict `MSTR_REGSESSION_PUBLIC_CORE_SOURCE_PASS`
- source verification date `2026-09-30`

The source-verification date is excluded from outcomes.

## Frozen sample

Weekday sessions:
`2026-09-09 ... 2026-10-02`

Exclude:
`2026-09-30`

Signal window:
`14:31 ... 18:44 UTC`

Closed 1-minute candles only.
A candle starting at minute `s` becomes observable at `s+60s`.

No forward fill, interpolation or nearest-neighbor matching.

External return:
`mean(Binance MSTRUSDT 1m return, Bitget MSTRUSDT 1m return)`

MEXC return:
`MSTRSTOCK_USDT 1m return`

Lag gap:
`external_return - mexc_return`

Direction:
`FOLLOW_EXTERNAL_CONSENSUS`

## Alpha budget

Total:
`0.05`

Pre-outcome split:
- exact already-replicated 5/3/1m transfer: `0.025`
- separate exploratory 64-cell grid: `0.025`

The split cannot be changed after outcomes.

## Confirmatory transfer

Exact rule already surviving NVIDIA, TESLA and COINBASE:
- shock >=5 bps
- lag gap >=3 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS
- 1-minute cooldown

PASS requires:
- N >=50
- signals on >=12 sessions
- mean gross >0
- median gross >0
- win rate >50%
- all chronological thirds mean >0
- exact one-sided binomial p <0.025

If PASS:
`FOUR_ASSET_REPLICATION_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

## Exploratory MSTR grid

Frozen grid:
- shock 5 / 10 / 20 / 40 bps
- lag gap 3 / 5 / 10 / 20 bps
- horizon 1 / 2 / 5 / 15 minutes
- 64 cells
- cooldown equals horizon

Pre-Holm eligibility:
- N >=20
- mean gross >0
- median gross >0
- win rate >50%
- all chronological thirds mean >0

Holm-Bonferroni FWER:
`0.025`

## Costs

Report:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 18 / 20 bps.

Costs do not decide scientific survival.

## No rescue

After outcomes open, do not alter alpha split, sources, session window, thresholds, horizons, direction, N/stability gates or excluded source day.

No retrospective OOS, private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
