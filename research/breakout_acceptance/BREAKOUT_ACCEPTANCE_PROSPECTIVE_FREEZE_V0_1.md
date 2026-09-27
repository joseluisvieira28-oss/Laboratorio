# BREAKOUT-ACCEPTANCE-001 — PROSPECTIVE FREEZE V0.1

Date: 2026-09-27
Status: FROZEN BEFORE ECONOMIC OUTCOME ACCESS
Candidate: BAV-ARQ018-4H-H48-001
Ancestry: ARQ-018 BREAKOUT + VOLUME + ATR (pre-existing IDEA_ONLY)
Parent PBR credit: ZERO

## Hypothesis
A 4H range escape with unusually strong participation, followed by two consecutive closes that remain above the old range, represents acceptance into a new price region and may contain 48-hour continuation information.

## Universe and source
Venue: Binance Spot.
Official market-data-only REST host: data-api.binance.vision.
Symbols: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT.
Bar interval: 4H UTC.
Only completed bars may be used.

## Deterministic state
For each completed candidate breakout bar:
1. prior_range_high = maximum HIGH of the strictly prior 60 completed 4H bars.
2. prior_atr14 = Wilder ATR14 computed only from completed bars strictly before the breakout bar.
3. breakout requires breakout CLOSE > prior_range_high + 0.25 * prior_atr14.
4. participation requires breakout VOLUME >= empirical 75th percentile of VOLUME across the strictly prior 60 completed bars.
5. freeze the old prior_range_high at the breakout.
6. acceptance requires BOTH of the next two completed 4H bars to CLOSE strictly above that frozen old range high.
7. entry observation = OPEN of the immediately following completed 4H interval after acceptance is known.
8. exit observation = OPEN exactly 12 completed 4H bars later (48 hours).
9. direction = LONG only.
10. one active observation per symbol; overlapping same-symbol signals are ignored.

No retest is required. No PBR zone, PBR stop, PBR target, 3R exit or PBR winner/loser label is used.

## Friction
BASE round-trip cost: 20 bps.
STRESS round-trip cost: 30 bps.
No leverage. No stop. No target.

## Prospective boundary
No entry before 2026-09-28T00:00:00Z may count.
Pre-boundary bars may be used only as deterministic indicator warmup.
Historical PBR outcomes and protected PBR periods may not validate this successor.

## Maturity
Descriptive checkpoint: 20 resolved observations.
Formal review: >=40 resolved observations AND >=8 full calendar weeks from boundary AND >=3 represented symbols.
Until then: INSUFFICIENT_MATURITY, never promotion and never NO_EDGE solely for small N.

## Formal requirements
At maturity:
- BASE mean net return > 0;
- BASE PF > 1;
- STRESS mean net return > 0;
- at least 3 symbols represented;
- zero source/timing deviations.

Bootstrap/p-values are diagnostics, not standalone terminal vetoes.
No early promotion.

## Firewalls
Research/shadow only.
No live trading, orders, exchange mutation, wallets, leverage, deployment or main merge.
No post-outcome tuning. Scientific changes require a new identity.
