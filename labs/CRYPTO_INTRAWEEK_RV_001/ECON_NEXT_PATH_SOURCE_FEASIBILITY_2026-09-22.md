# CIRV ECONOMIC TRANSLATION — NEXT PATH SOURCE FEASIBILITY — 2026-09-22

## STATUS

**SOURCE_FEASIBILITY_BLOCKED_NO_FREE_FULL_HISTORICAL_EXECUTABLE_BBO**

Research-only. No option prices, strategy returns, PnL, 2025/2026 outcomes, live trading, orders, wallets or exchange mutation were opened by this feasibility note.

## Context

Parent forecasting mechanism:
- CRYPTO-INTRAWEEK-RV-001 / CIRV-HAR-DOW-BTCETH-001
- L5 replicated OOS forecast mechanism, M6 forward/radar shadow.

First economic translation:
- CIRV-VOLTARGET-BTCETH-SPOT-001
- Prospectively frozen before outcomes.
- 2023 Discovery terminal: DISCOVERY_FAIL_NO_PROMOTION.
- 2024 replication and 2025 OOS remain unopened.

## Next materially distinct economic translation

The economically direct use of a realized-variance forecast is an ex-ante variance-premium decision:
- compare executable option implied variance to the CIRV forecast of subsequently realized variance;
- use a prospectively frozen delta-hedged option implementation;
- require historical executable bid/ask and size, not marks, current labels, midpoints or synthetic fills.

This would be a **new candidate**, not a rescue of the failed spot vol-target path and not a rewrite of BTC-OPTIONS-VRP-001.

## Existing project evidence

The Crypto Lab already established:
- BTC-OPTIONS-VRP-001: DISCOVERY_PASS_VRP_EXISTS, strategy not automatically authorized.
- Historical public trade-print execution MVE was EXECUTION_DATA_LIQUIDITY_INSUFFICIENT (19/120 executable episodes).
- Frozen CoinAPI BBO source probe stopped at HTTP 403 / credential required before usable BBO metadata.
- Tardis sample Source Gate passed, but full-history access remains access/cost gated.
- Existing exact execution path must not be rescued by mark/mid/synthetic fills.

## Current public-source recheck — 2026-09-22

Tardis official documentation:
- Deribit historical market data including options is available from 2019-03-30.
- options_chain and quotes are available for Deribit OPTIONS.
- only historical datasets for the **first day of each month** are downloadable without an API key.
- full date-range download requires the Tardis historical-data access path.

Bybit official documentation:
- current option orderbook snapshots are publicly queryable;
- recent public option trades are queryable and archived historical trades may be downloadable;
- these routes do not establish a free full historical option BBO/size corpus equivalent to the required executable quote history.
- Bybit historical-volatility endpoint has only the last two years and is not contract-level executable BBO history.

## Classification

**BLOCKED_SOURCE — NOT NO_EDGE.**

No CIRV-informed options economic outcome may be opened using:
- current order books as historical proxies;
- mark prices as fills;
- midpoints as fills;
- sparse first-day-of-month samples as if they were full chronology;
- the previously failed trade-print MVE as a rescue;
- paid data without separate operator authorization.

## Smallest legitimate unlock

One of:
1. authorized full historical Deribit/OKX option BBO + size access with a separately frozen CIRV-options execution protocol; or
2. a prospectively collected public option BBO corpus, with the evidence window frozen before outcomes.

Until one of those exists, CIRV remains a validated volatility-forecast / risk-information motor, **not a standalone trade-authorized strategy**.

## Public documentation checked

- https://docs.tardis.dev/historical-data-details/deribit
- https://docs.tardis.dev/downloadable-csv-files
- https://docs.tardis.dev/downloadable-csv-files/overview
- https://bybit-exchange.github.io/docs/v5/market/orderbook
- https://bybit-exchange.github.io/docs/v5/market/recent-trade
- https://bybit-exchange.github.io/docs/v5/market/iv
