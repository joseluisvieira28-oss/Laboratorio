# MEXC-HL-SP500-LEADLAG-001 — PRE-OUTCOME FREEZE V0.4

Date: 2026-10-04
Status: FROZEN BEFORE HISTORICAL CROSS-VENUE OUTCOMES

## Source binding

MEXC: `SPX500_USDT`
Hyperliquid: `xyz:SP500` on DEX `xyz`

The binding was resolved at source level before historical lead/lag scoring. The earlier source-only probe opened no historical outcomes.

## Economic mechanism

MEXC declares Hyperliquid as the SP500 index origin.

Hypothesis:

> a sufficiently large 1-minute move on Hyperliquid that is not yet matched by the MEXC traded contract may create a short-lived MEXC catch-up move in the same direction.

This is an information-propagation hypothesis, not a generic chart pattern.

## Frozen data window

Discovery only:

`2026-10-01T00:00:00Z <= observable t < 2026-10-04T09:00:00Z`

No data at or after 09:00 UTC on 2026-10-04 may enter V0.4.

This window was not scored before the freeze.

## Clock

Both legs use closed 1-minute candles.

MEXC raw bucket start `s` is observable at `s+60s`.

Hyperliquid candle open `t` is observable at `t/1000+60s`.

Only exact observable-minute matches are allowed.

## Frozen signal

At observable minute `t`:

`hl_ret = 10000 * (HL_close[t] / HL_close[t-1] - 1)`

`mexc_ret = 10000 * (MEXC_close[t] / MEXC_close[t-1] - 1)`

`lag_gap = hl_ret - mexc_ret`

Signal exists only when all are true:

1. `abs(hl_ret) >= shock_threshold`
2. `sign(lag_gap) == sign(hl_ret)`
3. `abs(lag_gap) >= gap_threshold`

Direction is fixed to `FOLLOW_HYPERLIQUID`.

No fade alternative may be added after outcomes.

## Frozen grid

Hyperliquid 1m shock thresholds:
- 5 bps
- 10 bps
- 20 bps

Lag-gap thresholds:
- 3 bps
- 5 bps
- 10 bps

MEXC outcome horizons:
- 1 minute
- 2 minutes
- 5 minutes
- 15 minutes

36 cells total.

Per-cell overlap cooldown equals the horizon.

## Discovery gate

A cell is pre-Holm eligible only if:
- N >= 20 non-overlapping signals;
- mean gross signed MEXC return > 0 bps;
- win rate > 50%;
- mean gross signed return > 0 in every chronological discovery third;
- exact one-sided binomial p-value vs 50% is defined.

Holm-Bonferroni controls family-wise alpha at 0.05 over all eligible cells.

## Costs

Costs do NOT decide existence of the scientific discovery signal.

For every cell report illustrative mean net bps at:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps round-trip.

12/14/16 bps are included because the current public MEXC API tariff implies those approximate fee-only round-trip combinations for maker-maker / maker-taker / taker-taker.

## Promotion ceiling

A Holm-selected cell is only:

`CROSSVENUE_DISCOVERY_CANDIDATE_ONLY`

V0.4 has NO retrospective OOS authority.

No live trading, account read, wallet, private endpoint, order or exchange mutation is authorized.

## No rescue

After outcomes are opened V0.4 may not:
- change source binding;
- add another Hyperliquid S&P proxy;
- lower shock/gap thresholds;
- change horizons;
- switch direction;
- select a subperiod;
- relax Holm or stability gates.

Any follow-up requires a new pre-outcome freeze and untouched data.
