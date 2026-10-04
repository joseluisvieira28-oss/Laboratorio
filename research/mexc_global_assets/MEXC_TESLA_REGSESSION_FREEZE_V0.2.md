# MEXC TESLA REGULAR-SESSION PACK — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE TESLA OUTCOMES

## Source authority

Target:
- MEXC `TESLA_USDT`

External public legs:
- Binance Futures `TSLAUSDT`
- Bitget Futures `TSLAUSDT`

MEXC declared index origins:
- BINANCE_FUTURE
- BITGET_FUTURE
- BINANCETICKER
- PYTH
- KAIKO

Source gate:
- run `37229205842`
- verdict `TESLA_REGSESSION_PUBLIC_CORE_SOURCE_PASS`
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

External 1-minute return:
`mean(Binance TSLAUSDT return, Bitget TSLAUSDT return)`

MEXC 1-minute return:
`TESLA_USDT close-to-close return`

Lag gap:
`external_return - mexc_return`

A signal requires:
- `abs(external_return) >= shock_threshold`
- `sign(lag_gap) == sign(external_return)`
- `abs(lag_gap) >= gap_threshold`

Direction:
`FOLLOW_EXTERNAL_CONSENSUS`

## Family-wise error budget

Total alpha budget:
`0.05`

Split before outcomes:
- confirmatory NVDA-rule transfer: `0.025`
- exploratory TESLA grid: `0.025`

This split is frozen and cannot be reallocated after outcomes.

## Family A — confirmatory cross-asset transfer

Family:
`MEXC-TESLA-NVDA-RULE-TRANSFER-001`

This copies exactly the sole NVIDIA V0.5 Holm survivor:

- shock >= 5 bps
- lag gap >= 3 bps
- horizon = 1 minute
- FOLLOW_EXTERNAL_CONSENSUS
- 1-minute cooldown

PASS requires all:
- N >= 50
- signals on at least 12 distinct sessions
- mean gross > 0
- median gross > 0
- win rate > 50%
- all three chronological thirds mean > 0
- exact one-sided binomial p < 0.025

There is exactly one confirmatory transfer test.

If PASS:
`CROSS_ASSET_REPLICATION_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

## Family B — exploratory TESLA grid

Family:
`MEXC-TESLA-REGSESSION-LEADLAG-DISCOVERY-001`

Frozen grid:
- shock: 5 / 10 / 20 / 40 bps
- lag gap: 3 / 5 / 10 / 20 bps
- horizon: 1 / 2 / 5 / 15 minutes
- 64 cells

Per-cell cooldown equals horizon.

A cell is pre-Holm eligible only if:
- N >= 20
- mean gross > 0
- median gross > 0
- win rate > 50%
- all chronological thirds mean > 0

Exact one-sided binomial p-values are computed.

Holm-Bonferroni controls FWER at:
`0.025`

Any selected exploratory cell is only:
`TESLA_REGSESSION_DISCOVERY_CANDIDATE_ONLY`

## Outcome

For signal side `sign(external_return)`:

`gross_signed_bps = side * 10000 * (MEXC_close[t+h] / MEXC_close[t] - 1)`

Gross scientific return only.

## Costs

Illustrative round-trip scenarios:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Costs are not a scientific survival gate.

## No rescue

After outcomes open, do not:
- change alpha split;
- change source legs;
- change session window;
- add/remove thresholds or horizons;
- change direction;
- alter N/stability gates;
- reinclude 2026-09-30;
- select favorable dates.

No retrospective OOS, private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
