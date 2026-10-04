# MEXC-NVDA-BITGET-LEADLAG-001 — PRE-OUTCOME FREEZE V0.7

Date: 2026-10-04
Status: FROZEN BEFORE OCTOBER CROSS-VENUE OUTCOMES

## Source authority

Leader:
- Bitget USDT-FUTURES `NVDAUSDT`

Follower / execution research leg:
- MEXC `NVIDIA_USDT`

MEXC public contract metadata explicitly lists `BITGET_FUTURE` among the NVIDIA index origins.

V0.6.1 source gate passed:
- MEXC live: 234.84
- Bitget live: 234.85
- live dispersion: ~0.4258 bps
- public 1m candles: PASS
- outcomes opened before this freeze: 0

## Economic mechanism

NVIDIA is more volatile than the SP500 index.

Hypothesis:

> a sufficiently large 1-minute Bitget NVDA move that MEXC has not yet fully matched may be followed by a same-direction MEXC catch-up move.

This is a cross-venue information-propagation hypothesis.

## Discovery window

`2026-10-01T00:00:00Z <= observable t < 2026-10-04T09:00:00Z`

This cross-venue window was not scored before this freeze.

No data at or after 09:00 UTC on 2026-10-04 may enter V0.7.

## Frozen signal

At observable minute `t`:

`leader_ret = 10000 * (Bitget_close[t] / Bitget_close[t-1m] - 1)`

`mexc_ret = 10000 * (MEXC_close[t] / MEXC_close[t-1m] - 1)`

`lag_gap = leader_ret - mexc_ret`

Signal requires:
1. `abs(leader_ret) >= shock_threshold`
2. `sign(lag_gap) == sign(leader_ret)`
3. `abs(lag_gap) >= gap_threshold`

Direction is fixed:
`FOLLOW_BITGET`

No FADE alternative is authorized.

## Frozen grid

Leader shock thresholds:
- 10 bps
- 20 bps
- 40 bps

Lag-gap thresholds:
- 5 bps
- 10 bps
- 20 bps

MEXC horizons:
- 1 minute
- 2 minutes
- 5 minutes
- 15 minutes

36 cells.

Per-cell cooldown equals horizon.

## Discovery gate

Pre-Holm eligibility requires:
- N >= 20 non-overlapping signals;
- mean gross signed MEXC return > 0;
- win rate > 50%;
- every chronological discovery third has mean gross > 0;
- exact one-sided binomial p-value is defined.

Holm-Bonferroni:
- family-wise alpha = 0.05.

## Execution relevance

Costs do NOT determine whether a scientific signal exists.

Every cell must report net sensitivity at:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps round-trip.

12/14/16 bps are economic reference points for the currently published standard MEXC API fee combinations.

A cell with gross mean below those values may still be scientifically interesting but is not automatically execution-viable.

## Promotion ceiling

Holm-selected cells become only:
`NVDA_CROSSVENUE_DISCOVERY_CANDIDATE_ONLY`

No retrospective OOS is authorized by V0.7.

## No rescue

After outcomes are opened, do not:
- lower thresholds;
- change horizons;
- switch direction;
- choose subperiods;
- change source;
- weaken stability or Holm gates.

Any follow-up requires a new pre-outcome freeze and untouched sample.

No live trading, accounts, wallets, private endpoints, orders or mutation are authorized.
