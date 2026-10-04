# MEXC NVIDIA REGULAR-SESSION LEAD-LAG — PRE-OUTCOME FREEZE V0.5

Date: 2026-10-04
Status: FROZEN BEFORE REGULAR-SESSION OUTCOMES

Target: MEXC `NVIDIA_USDT`.

External public legs:
- Binance Futures `NVDAUSDT`
- Bitget Futures `NVDAUSDT`

Source gate:
- run `37227306368`
- verdict `NVIDIA_REGSESSION_SOURCE_PASS`
- verification day `2026-09-30`, excluded from outcomes.

Discovery dates:
`2026-09-09 ... 2026-10-02`, weekdays, excluding `2026-09-30`.

Signal window:
`14:31 <= observable t <= 18:44 UTC`.

This keeps every frozen horizon inside the regular-session interior and away from the already-tested cash-open / cash-close transition windows.

All legs use closed 1-minute prices. A raw candle starting at minute `s` becomes observable at `s+60s`.

No forward fill, interpolation or nearest-neighbor alignment.

External return:
`mean(Binance_1m_return_bps, Bitget_1m_return_bps)`.

MEXC return:
`MEXC 1m close-to-close return in bps`.

Lag gap:
`external_return_bps - mexc_return_bps`.

Signal requires:
1. `abs(external_return_bps) >= shock_threshold`
2. `sign(lag_gap_bps) == sign(external_return_bps)`
3. `abs(lag_gap_bps) >= gap_threshold`

Direction is fixed to:
`FOLLOW_EXTERNAL_CONSENSUS`.

Frozen grid:
- shock: 5 / 10 / 20 / 40 bps
- lag gap: 3 / 5 / 10 / 20 bps
- horizon: 1 / 2 / 5 / 15 minutes
- 64 cells total
- per-cell cooldown equals horizon

Outcome:
`side * 10000 * (MEXC_close[t+h] / MEXC_close[t] - 1)`.

Discovery eligibility requires:
- N >= 20
- mean gross signed return > 0
- median gross signed return > 0
- win rate > 50%
- each chronological third mean > 0
- exact one-sided binomial p-value defined

Holm-Bonferroni controls family-wise alpha 0.05 across all 64 frozen cells.

Illustrative round-trip costs:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Costs are reported separately from scientific survival.

Promotion ceiling:
`NVIDIA_REGSESSION_DISCOVERY_CANDIDATE_ONLY`.

No retrospective OOS and no parameter rescue are authorized.

After outcomes are opened, do not change thresholds, gaps, horizons, direction, session window, external legs, N gate, stability gate or multiple-testing rule.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
