# MEXC-GOLD-BITGET-LEADLAG-001 — PRE-OUTCOME FREEZE V0.9

Date: 2026-10-04
Status: FROZEN BEFORE OCTOBER CROSS-VENUE OUTCOMES

## Source authority

Leader: Bitget USDT-FUTURES `XAUUSDT`
Follower/research execution leg: MEXC `XAU_USDT`

V0.8 source gate passed before this freeze:
- MEXC live: 4145.50
- Bitget live: 4144.54
- dispersion: ~2.3163 bps
- public 1m candles: PASS
- MEXC declares `BITGET_FUTURE`: PASS
- outcomes opened: 0

## Mechanism

Gold is a distinct family from the prior SP500 and NVIDIA experiments.

Hypothesis: a sufficiently large 1-minute Bitget XAU move that MEXC has not fully matched may be followed by a same-direction MEXC catch-up move.

Direction is fixed to `FOLLOW_BITGET`.

## Discovery window

`2026-10-01T00:00:00Z <= observable t < 2026-10-04T09:00:00Z`

No data at or after 09:00 UTC on 2026-10-04 may enter V0.9.

## Frozen signal

`leader_ret = 10000 * (Bitget_close[t] / Bitget_close[t-1m] - 1)`

`mexc_ret = 10000 * (MEXC_close[t] / MEXC_close[t-1m] - 1)`

`lag_gap = leader_ret - mexc_ret`

Signal requires:
1. `abs(leader_ret) >= shock_threshold`
2. `sign(lag_gap) == sign(leader_ret)`
3. `abs(lag_gap) >= gap_threshold`

## Frozen grid

Leader shock thresholds: 3 / 5 / 10 bps  
Lag-gap thresholds: 2 / 3 / 5 bps  
MEXC horizons: 1 / 2 / 5 / 15 minutes

36 cells total. Per-cell cooldown equals horizon.

The lower ex-ante thresholds relative to NVDA reflect the lower expected 1-minute volatility of gold and were fixed before opening GOLD outcomes.

## Discovery gate

Pre-Holm eligibility requires:
- N >= 20 non-overlapping signals;
- mean gross signed MEXC return > 0;
- win rate > 50%;
- every chronological discovery third mean gross > 0;
- exact one-sided binomial p-value is defined.

Holm-Bonferroni controls family-wise alpha at 0.05.

## Cost reporting

Costs do not define scientific edge.

Report mean net sensitivity at round-trip costs:
0 / 1 / 2 / 4 / 5 / 10 / 12 / 16 bps.

## Promotion ceiling

A Holm-selected cell becomes only:
`GOLD_CROSSVENUE_DISCOVERY_CANDIDATE_ONLY`

No retrospective OOS is authorized.

## No rescue

After outcomes are opened, V0.9 may not change:
- source;
- direction;
- thresholds;
- horizons;
- overlap;
- discovery window;
- stability gates;
- Holm correction.

No accounts, wallets, private endpoints, orders, mutation or live trading are authorized.
