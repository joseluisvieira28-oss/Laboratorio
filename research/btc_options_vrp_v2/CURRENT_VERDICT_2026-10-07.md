# BTC-OPTIONS-VRP-001 — V2 CURRENT VERDICT 2026-10-07

## Canonical current state
**ACCESSIBILITY_UNRESOLVED / UNDERPOWERED_PRE / SOURCE_HEALTH_PASS**

This is the legitimate V2 verdict today.

It is NOT:
- SURVIVES;
- NO_EDGE_AT_H;
- micro-live eligible;
- execution-profitability proven.

## Gates
- Economic mechanism: PASS — volatility/risk-transfer premium.
- Public source/instrument mechanics: PASS.
- Operator execution accessibility: UNRESOLVED. Current Standard Margin order-of-magnitude is ~0.0365 BTC for the 0.1+0.1 ATM option pair before hedge margin.
- Current public BBO source health: PASS.
- Current source-health canonical run: 37659393449.
- Current source-health artifact: 11499987991.
- Captured instruments: 74.
- Failures: 0.
- Authentication/orders/PnL/returns: NONE.
- Old rigid 25–35 DTE source geometry: zero current pairs.
- V2 source geometry: amended before outcomes to available expiry nearest 30 DTE inside 14–60 DTE.
- Power: UNDERPOWERED_PRE because V2 forward N=0.
- The previous raw-N=36 / N_eff=30 activation target is REVOKED pre-outcome because it normalized power to an arbitrary 1 BTC denominator rather than required risk capital.
- Capital-normalized planning using the current Standard Margin scale implies that a modest 10%→20% annual-return superiority question would require thousands of effective weekly observations.
- No forward performance outcome is authorized under the current weekly design.

## Forward rule
One non-overlapping weekly cohort at Thursday 08:00 UTC.
The source-only collector may record entry/exit BBO, sizes, timestamps, index and hedge reference.
It MUST NOT compute return/PnL/expectancy before activation.

## Activation
Next legitimate stage:
1. redesign the execution-validation estimand for information efficiency while remaining in the same VRP economic family;
2. freeze capital/risk denominator and power before any new forward outcome;
3. keep source-only BBO evidence outcome-blind;
4. only a new V2 activation freeze may ever open performance;
5. final result remains SURVIVES / NO_EDGE_AT_H / INCONCLUSIVE.

## Safety
No main merge.
No live trading.
No orders.
No private endpoints/account reads.
No wallets.
No payment.
No post-outcome rescue.
