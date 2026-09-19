# BTC-OPTIONS-VRP-BINANCE-001 — DISCOVERY ACTIVATION RECEIPT V0.1

Date: 2026-09-19
MVE: `BOVRP-ATM30-24H-STRADDLE-CARRY-001`

All frozen prerequisites have now passed before economic outcomes are opened:

- options source: `BINANCE_EOH_SOURCE_FEASIBLE`
- 24h geometry: `PREDISCOVERY_GEOMETRY_PASS`
- BTCUSDT spot 1m source: `BINANCE_SPOT1M_SOURCE_FEASIBLE`
- BTCUSDT index 1m source: `BINANCE_INDEX1M_SOURCE_FEASIBLE`

The pre-freeze remains binding.

Technical definitions frozen before the first economic run:
- profit factor = sum(positive net cash PnL) / abs(sum(negative net cash PnL));
- positive month = arithmetic mean of primary net premium returns in that UTC calendar month > 0;
- leave-one-month-out statistic = arithmetic mean of all primary observations after removing that month;
- bootstrap = circular moving-block bootstrap of the primary net premium-return sequence, block length 5 observations, 10,000 replications, seed 230911;
- 95% CI = empirical 2.5% and 97.5% bootstrap quantiles;
- CVaR 5% = arithmetic mean of the worst max(1, ceil(0.05*N)) primary net premium returns;
- losing streak = maximum consecutive observations with net cash PnL < 0.

Only the primary 15-31 DTE stratum is adjudicative in V0.1. The predeclared secondary term-structure strata are not opened in this run because their exact within-bin target-DTE selection was not separately frozen. They cannot rescue the primary.

No rule may be changed after this activation based on observed outcomes.
