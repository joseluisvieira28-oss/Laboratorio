# MEXC APPLE REGULAR-SESSION TRANSFER — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE APPLE OUTCOMES

## Purpose

Test whether the exact regular-session lead-lag cell that survived NVIDIA V0.5 and replicated on TESLA V0.2 also transfers to APPLE.

This is not a new grid search.

## Source authority

Target:
- MEXC `AAPLSTOCK_USDT`

External public legs:
- Binance Futures `AAPLUSDT`
- Bitget Futures `AAPLUSDT`

MEXC declared index origins:
- BINANCE_FUTURE
- BITGET_FUTURE
- BINANCETICKER
- PYTH
- KAIKO

Source gate:
- run `37229730285`
- verdict `APPLE_REGSESSION_PUBLIC_CORE_SOURCE_PASS`
- verification date `2026-09-30`

The source-verification date is excluded from outcomes.

## Frozen sample

Weekday sessions:
`2026-09-09 ... 2026-10-02`

Exclude:
`2026-09-30`

Signal window:
`14:31 ... 18:44 UTC`

Exact closed 1-minute alignment only.
No forward fill.
No interpolation.

## Exact transferred cell

External return:
`mean(Binance AAPLUSDT 1m return, Bitget AAPLUSDT 1m return)`

MEXC return:
`AAPLSTOCK_USDT 1m return`

Lag gap:
`external_return - mexc_return`

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

No alternative threshold, horizon or direction is authorized.

## Sequential cross-asset alpha control

TESLA replication used alpha:
`0.025`

APPLE replication uses:
`0.0125`

If another independent asset is tested after APPLE, its alpha ceiling is:
`0.00625`

This prevents repeated asset testing from being treated as independent 5% shots.

## PASS gate

PASS requires all:
- N >= 50
- signals on at least 12 distinct sessions
- mean gross > 0
- median gross > 0
- win rate > 50%
- all three chronological thirds mean > 0
- exact one-sided binomial p < 0.0125

If insufficient N/session coverage:
`APPLE_TRANSFER_UNDERPOWERED`

If adequately powered but any gate fails:
`APPLE_TRANSFER_FAIL`

If all pass:
`THIRD_ASSET_TRANSFER_REPLICATION_PASS__FORWARD_VALIDATION_REQUIRED`

## Costs

Report round-trip scenarios:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Costs are not a scientific survival gate.

## Governance

No retrospective OOS.
No post-outcome tuning.
No private endpoints.
No account reads.
No wallets.
No orders.
No exchange mutation.
No live trading.
