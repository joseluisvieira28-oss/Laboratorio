# BTC-OPTIONS-VRP-001 — V2 CURRENT VERDICT 2026-10-07

## Canonical current state
**UNDERPOWERED_PRE / FORWARD_SOURCE_BUILD_AUTHORIZED**

This is the legitimate V2 verdict today.

It is NOT:
- SURVIVES;
- NO_EDGE_AT_H;
- micro-live eligible;
- execution-profitability proven.

## Gates
- Economic mechanism: PASS — volatility/risk-transfer premium.
- Accessibility at public-source/instrument-mechanics level: PASS.
- Current public BBO source health: PASS.
- Current source-health canonical run: 37659393449.
- Current source-health artifact: 11499987991.
- Captured instruments: 74.
- Failures: 0.
- Authentication/orders/PnL/returns: NONE.
- Old rigid 25–35 DTE source geometry: zero current pairs.
- V2 source geometry: amended before outcomes to available expiry nearest 30 DTE inside 14–60 DTE.
- Power: UNDERPOWERED_PRE because V2 forward N=0.
- Raw complete-cohort target: 36.
- Blind effective-N activation floor: 30.
- Frozen H: 18.2954 bps stress-net return per seven-day episode.
- Frozen design alternative: 35.0270 bps per seven-day episode.
- Planned power at N_eff=30 using 50%-inflated legacy nuisance dispersion: 0.8458.

## Forward rule
One non-overlapping weekly cohort at Thursday 08:00 UTC.
The source-only collector may record entry/exit BBO, sizes, timestamps, index and hedge reference.
It MUST NOT compute return/PnL/expectancy before activation.

## Activation
After at least 36 raw complete cohorts:
1. blind source-integrity audit;
2. blind N_eff/dependence re-estimation without forward mean;
3. require N_eff >=30 and power >=0.80 under the unchanged freeze;
4. commit a separate activation freeze;
5. only then open the one-shot performance outcome;
6. classify mechanically as SURVIVES / NO_EDGE_AT_H / INCONCLUSIVE.

## Safety
No main merge.
No live trading.
No orders.
No private endpoints/account reads.
No wallets.
No payment.
No post-outcome rescue.
