# MEXC EVENT FUTURES LAB — PREMIUM BASIS V1.2 FINAL HOLDOUT FREEZE

Date: 2026-10-02
Status: PRE-HOLDOUT / RESEARCH-ONLY / FAIL-CLOSED

## Parent

Parent experiment:
`MEXC_EVENT_FUTURES_PREMIUM_BASIS_V1.1`

Parent result before opening this holdout:
- 120 frozen discovery cells;
- 9 basic discovery-eligible;
- 5 Benjamini-Hochberg FDR q=0.05 selected;
- all 5 passed August 2026 OOS;
- all 5 are MUUSDT FOLLOW_PREMIUM cells;
- September 2026 was not fetched by V1.1.

No other V1.1 cell may be opened in this final holdout.

## Exact five frozen holdout cells

1. MUUSDT / 10m / |z_premium| >= 1.0 / FOLLOW_PREMIUM
2. MUUSDT / 10m / |z_premium| >= 1.5 / FOLLOW_PREMIUM
3. MUUSDT / 10m / |z_premium| >= 2.0 / FOLLOW_PREMIUM
4. MUUSDT / 30m / |z_premium| >= 1.5 / FOLLOW_PREMIUM
5. MUUSDT / 30m / |z_premium| >= 2.0 / FOLLOW_PREMIUM

No threshold interpolation, no alternative mode, no other horizon, no other asset.

## Holdout window

Final historical holdout:
2026-09-01T00:00:00Z <= t < 2026-10-01T00:00:00Z

Warm-up source strictly before holdout is allowed only to initialize the same trailing 24h premium z-score.

## Source and clock — unchanged

Symbol:
`MUSTOCK_USDT`

Index:
`https://contract.mexc.com/api/v1/contract/kline/index_price/MUSTOCK_USDT`

Fair price:
`https://contract.mexc.com/api/v1/contract/kline/fair_price/MUSTOCK_USDT`

Interval:
`Min5`

Every raw Min5 close timestamp `s` maps to observable time `s + 300 seconds`.

Feature, trailing window, z-score, signal direction, entry alignment, target-price definition and tie treatment are identical to V1.1.

## Product relevance already established before holdout

Current Event Futures product matrix independently showed MUUSDT currently offers:
- 10m
- 30m
- 1H
- 4H

Two separate current product snapshots before this freeze observed:
- MUUSDT Up payout = 80%
- MUUSDT Down payout = 80%

V0.6.4.2 also passed the current Event Futures display-vs-public-index equivalence candidate gate:
- 60/60 valid paired observations across the five product underlyings;
- 100% within 1.0 bp;
- median difference 0.0 bp.

These facts do NOT prove historical payout or expiry settlement equivalence.

## Final holdout multiplicity

There are exactly 5 holdout hypotheses.

For each cell compute:
- non-tie N;
- directional accuracy;
- Wilson 95% lower bound;
- one-sided exact binomial p-value vs p0 = 55.5555556%;
- EV at 80% payout;
- EV at 70% payout;
- required payout for zero EV.

Apply **Holm-Bonferroni family-wise error control alpha=0.05** across all 5 raw holdout p-values.

A cell survives only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- EV80 > 0;
- Holm-adjusted p <= 0.05.

Family verdict:
- `FINAL_HOLDOUT_SURVIVOR` if at least one frozen cell survives Holm;
- otherwise `NO_SURVIVOR_FINAL_HOLDOUT`.

Because the five thresholds are nested/correlated, report all five; do not select a prettier threshold after the holdout.

## Hard boundaries

- September may be opened only by this frozen V1.2 evaluator.
- No October outcome data.
- No rule changes after holdout.
- No payout-history fabrication.
- No claim of exact Event Futures settlement equivalence.
- No authenticated exchange requests.
- No orders.
- No account mutation.
- No live trading.
- No merge to main.
