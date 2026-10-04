# MEXC-GOLD-CONSENSUS-LEADLAG-001 — PRE-OUTCOME FREEZE V0.8

Date: 2026-10-04
Status: FROZEN BEFORE GOLD DISCOVERY OUTCOMES

MEXC target: `XAU_USDT`.

External public source family:
- Binance Futures `XAUUSDT`
- Bitget Futures `XAUUSDT`
- Bybit Futures `XAUUSDT`

The source gate passed before this freeze. Historical transport was verified using 2026-09-30 only.

Discovery window:
`2026-10-01T00:00:00Z <= observable t < 2026-10-04T00:00:00Z`

No 04 October outcome may enter V0.8.

All legs use closed 1-minute prices. Raw minute start `s` becomes observable at `s+60s`. No forward fill, interpolation or nearest-neighbor matching.

External consensus return:
`median(Binance 1m return, Bitget 1m return, Bybit 1m return)`

MEXC contemporaneous return:
`10000 * (mexc_close[t] / mexc_close[t-1] - 1)`

Lag gap:
`consensus_bps - mexc_ret_bps`

Signal requires:
1. `abs(consensus_bps) >= shock_threshold`
2. `sign(lag_gap) == sign(consensus_bps)`
3. `abs(lag_gap) >= gap_threshold`

Direction is fixed to `FOLLOW_EXTERNAL_CONSENSUS`.

Frozen grid:
- external shock: 5 / 10 / 20 / 40 bps
- lag gap: 3 / 5 / 10 / 20 bps
- MEXC horizon: 1 / 2 / 5 / 15 minutes
- 64 cells total
- per-cell cooldown equals horizon

Outcome:
`side * 10000 * (MEXC_close[t+h] / MEXC_close[t] - 1)`

Discovery pre-Holm gate:
- N >= 20
- mean gross signed return > 0
- win rate > 50%
- all three chronological thirds mean gross > 0
- exact one-sided binomial p-value defined

Holm-Bonferroni family-wise alpha = 0.05.

Illustrative round-trip cost reporting:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Costs do not decide scientific survival.

Promotion ceiling:
`GOLD_CROSSVENUE_DISCOVERY_CANDIDATE_ONLY`

No retrospective OOS in V0.8. No parameter rescue after outcomes. No live trading authorization.
