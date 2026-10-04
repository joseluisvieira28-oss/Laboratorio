# MEXC COINBASE REGULAR-SESSION PACK — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE COINBASE OUTCOMES

## Source authority

Target:
- MEXC `COINBASE_USDT`

External public legs:
- Binance Futures `COINUSDT`
- Bitget Futures `COINUSDT`

MEXC declared index origins:
- BINANCE_FUTURE
- BITGET_FUTURE
- BINANCETICKER
- PYTH
- KAIKO

Source gate:
- run `37229510016`
- verdict `COINBASE_REGSESSION_PUBLIC_CORE_SOURCE_PASS`
- source verification date `2026-09-30`

The source-verification date is excluded from outcomes.

## Frozen sample

Weekday sessions:
`2026-09-09 ... 2026-10-02`

Exclude:
`2026-09-30`

Signal window:
`14:31 ... 18:44 UTC`

All legs use closed 1-minute candles.
A candle starting at minute `s` becomes observable at `s+60s`.

No forward fill.
No interpolation.
No nearest-neighbor matching.

External return:
`mean(Binance COINUSDT 1m return, Bitget COINUSDT 1m return)`

MEXC return:
`COINBASE_USDT 1m return`

Lag gap:
`external_return - mexc_return`

Signal requires:
- abs(external_return) >= shock threshold
- sign(lag gap) == sign(external return)
- abs(lag gap) >= gap threshold

Direction:
`FOLLOW_EXTERNAL_CONSENSUS`

## Family-wise alpha budget

Total alpha:
`0.05`

Frozen split:
- confirmatory transfer of the already-replicated NVIDIA/TSLA rule: `0.025`
- exploratory COINBASE grid: `0.025`

The split cannot be changed after outcomes.

## Family A — confirmatory three-asset transfer

Family:
`MEXC-COINBASE-NVDA-TSLA-RULE-TRANSFER-001`

Exact transferred rule:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS
- cooldown 1 minute

PASS requires:
- N >= 50
- signals on at least 12 distinct sessions
- mean gross > 0
- median gross > 0
- win rate > 50%
- all chronological thirds mean > 0
- exact one-sided binomial p < 0.025

If PASS:
`THREE_ASSET_REPLICATION_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

## Family B — exploratory COINBASE grid

Frozen grid:
- shock: 5 / 10 / 20 / 40 bps
- lag gap: 3 / 5 / 10 / 20 bps
- horizon: 1 / 2 / 5 / 15 minutes
- 64 cells

Per-cell cooldown equals horizon.

Pre-Holm eligibility requires:
- N >= 20
- mean gross > 0
- median gross > 0
- win rate > 50%
- all chronological thirds mean > 0

Holm-Bonferroni controls FWER at:
`0.025`

Any selected exploratory cell is only:
`COINBASE_REGSESSION_DISCOVERY_CANDIDATE_ONLY`

## Costs

Illustrative round-trip costs:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

The 12 bps standard API fee floor is reported descriptively.
Cost survival is not a scientific discovery gate.

## No rescue

After outcomes are opened, do not alter:
- alpha split
- source legs
- session window
- thresholds
- horizons
- direction
- N/stability gates
- excluded source-verification day

No retrospective OOS, private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
