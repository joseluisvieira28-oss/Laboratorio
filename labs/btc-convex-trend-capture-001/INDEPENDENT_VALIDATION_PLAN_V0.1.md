# BTC-CONVEX-TREND-CAPTURE-001 — INDEPENDENT VALIDATION PLAN V0.1

**Frozen:** 2026-09-23  
**Status:** PRE-OUTCOME VALIDATION PLAN  
**Applies after:** exact source/config recovery

## Stage R0 — Exact reproduction gate

Purpose: reproduce the supplied TradingView exports, not prove edge.

Required inputs:
- exact Pine source;
- exact strategy inputs;
- Pine version;
- symbol/feed;
- chart type;
- strategy properties including order-size mode/value;
- commission and slippage;
- Bar Magnifier setting;
- calc/process settings relevant to fills.

PASS requires, for each supplied timeframe:
- same long-only/other direction behavior;
- same closed-trade count: 5m=187, 15m=159, 4h=61;
- same current open-position identity where the export date permits;
- every entry and exit matched to the same strategy bar under the recovered TradingView execution configuration;
- no unexplained repaint/lookahead behavior;
- aggregate PnL and drawdown differences explainable only by display rounding.

If the source cannot reproduce the exports, classify:
**REPRODUCTION_FAIL**.

No parameter adjustment using the observed BTC outcomes is allowed to force a pass.

## Stage R1 — Portability audit before cross-asset outcomes

Before opening cross-asset results, classify every strategy parameter as:
- dimensionless/percentage;
- volatility-scaled;
- price/tick-specific;
- timeframe-specific;
- symbol-specific.

Cross-asset replication is permitted only if the original rule can be applied mechanically without retuning.

No conversion of an absolute BTC parameter into an optimized percentage after seeing another asset.

## Stage R2 — Frozen cross-asset replication

Conditional universe, only when the exact original mechanism is mechanically portable:
- ETHUSDT perpetual;
- SOLUSDT perpetual;
- BNBUSDT perpetual.

Rule:
- same source code;
- same direction logic;
- same eligible timeframes among 5m / 15m / 4h;
- same original parameters;
- no per-asset optimization;
- no choosing only the asset that works.

Historical window:
- use only periods for which the official exchange source has defensible coverage;
- common-period reporting is mandatory when comparing assets;
- each asset is reported separately and as an equal-weight family summary.

The exact acquisition dates and source hashes must be frozen before economic outcomes are computed.

This stage is independent replication evidence only if no cross-asset outcome has been inspected before the freeze.

## Stage R3 — Cost robustness

Two views are required:

1. **REPRODUCTION COSTS**
   - exact TradingView commission/slippage recovered from the original configuration.

2. **ECONOMIC COSTS**
   - a separately frozen BASE and STRESS execution model appropriate to the intended venue;
   - frozen before opening R2 outcomes;
   - no fee-tier rescue after results.

A strategy that survives only under unrealistically favorable execution cannot promote.

## Stage R4 — Tail-dependence stress

Pre-registered robustness outputs:
- full sample;
- remove largest winner;
- remove top 3 winners;
- year-by-year / regime slices;
- block bootstrap;
- contribution of top 1 / top 5 trades to gross profit;
- max drawdown;
- maximum losing streak.

These are diagnostics and rejection tests. They are not permission to redesign the rule after seeing which slice fails.

## Stage R5 — Prospective forward

If R0 reproduces and R2/R3 justify continued research:
- freeze the exact executable rule;
- begin BTC forward collection only after the forward-freeze timestamp;
- no retroactive 2026 backfill;
- no manual discretionary entries;
- shadow/research only until the governing promotion policy separately authorizes anything more.

Forward evidence generated before exact source recovery does not count as reproduction evidence.

## Stage R6 — Exit-innovation branch

Any new profit-protection or regime rule inspired by the seed MFE analysis is a **new child hypothesis**, not V5.

Examples include:
- breakeven after a favorable excursion;
- partial profit lock;
- regime gate;
- adaptive trailing activation.

Such a child hypothesis must:
1. be specified completely before opening its evaluation outcomes;
2. not use the already-observed BTC 2019-2026 seed period as independent evidence;
3. have a separate ID and evidence chain;
4. beat the original V5 baseline under the same cost/risk basis on untouched evidence.

## Promotion boundary

No result from R0 alone can promote the strategy.
No descriptive risk-sizing improvement can promote the strategy.
No post-hoc BTC exit optimization can promote the strategy.

Only independently validated, cost-robust evidence can open a later promotion decision.

No live trading, exchange mutation or main merge is authorized by this plan.
