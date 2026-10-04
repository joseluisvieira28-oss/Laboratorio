# MEXC-BITGET-GOLD-LEADLAG-001 — PRE-OUTCOME FREEZE V1.1

Date: 2026-10-04
Status: FROZEN BEFORE SEPTEMBER GOLD OUTCOMES

## Binding
MEXC `XAU_USDT` ↔ Bitget `XAUUSDT`
Source verdict: `MEXC_BITGET_GOLD_SOURCE_PASS`

MEXC public metadata explicitly includes `BITGET_FUTURE` in the XAU index origins.

## Contamination firewall
Earlier Global Asset GOLD research opened June-August data. V1.1 excludes those periods.
September 2026 was not fetched by that family and is the only retrospective window authorized here.

## Mechanism
A large one-minute XAU move on Bitget, with a smaller contemporaneous move in the same direction on MEXC, may precede a MEXC catch-up move.

Signal mode is fixed:
`FOLLOW_BITGET_UNDERREACTION`

## Frozen signal
For a fully closed aligned minute:
- `bitget_ret = 10000*(BG_close[t]/BG_close[t-1]-1)`
- `mexc_ret = 10000*(MEXC_close[t]/MEXC_close[t-1]-1)`
- `lag_gap = bitget_ret - mexc_ret`

Signal only when:
1. abs(Bitget return) >= frozen shock threshold;
2. lag-gap has the same sign as the Bitget return;
3. abs(lag-gap) >= frozen gap threshold.

Direction is always the Bitget move direction.

## Frozen grid
Shock thresholds: 5 / 10 / 20 / 40 bps
Lag-gap thresholds: 3 / 5 / 10 / 20 bps
Horizons: 1 / 2 / 5 / 15 minutes
64 cells.

## Entry proxy
Entry = MEXC open of the next one-minute candle after the signal candle closes.
This avoids same-close lookahead. It is still an optimistic price-only proxy; forward BBO/depth is required before execution promotion.

## Windows
Discovery: 2026-09-05 00:00 UTC <= t < 2026-09-20 00:00 UTC
OOS: 2026-09-20 00:00 UTC <= t < 2026-10-01 00:00 UTC
Hard boundary: 2026-10-01 00:00 UTC
October remains unopened.

## Gates
Discovery:
- N >= 30
- mean gross > 0
- win rate > 50%
- all chronological third means > 0
- Holm-Bonferroni FWER 0.05.

Only Holm-selected cells may open OOS.

OOS:
- N >= 15
- mean gross > 0
- win rate > 50%
- exact one-sided binomial p < 0.05
- both chronological half means >= 0.

## Economics
Report 0/2/5/10/12/14/16/20 bps round-trip cost scenarios.
12/14/16 bps are execution hurdle references, not scientific gates.

## No rescue
No post-outcome threshold/horizon/direction/period/entry-rule changes.

Promotion ceiling:
`GOLD_CROSSVENUE_OOS_SIGNAL_CANDIDATE`

No live trading, accounts, private endpoints, wallets, orders or exchange mutation.
