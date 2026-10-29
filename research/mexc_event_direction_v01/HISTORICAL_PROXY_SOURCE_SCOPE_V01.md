# MEXC Event Futures V0.1 historical proxy, 29 October 2026

**RESEARCH ONLY / PRIOR OBSERVED DISCOVERY / NO HISTORICAL EVENT FUTURES PNL**

This push-triggered GitHub Actions workflow is restricted to public standard MEXC futures index Min5 candles for BTC_USDT and ETH_USDT from 2026-03-31 (warm-up) until 2026-04-15 UTC (exclusive). Protected September 2026 history remains unopened. Data collection is GET only, without credentials, private endpoints, orders, account, wallet or expenses.

Frozen diagnostic baseline families: UP_ALWAYS, ROC3_CONT and ROC3_REV based only on the last 3 completed five-minute candles. Horizons: 10m, 30m, 60m, non-overlapping entry timestamps. Historical hypothetical entry price = INDEX candle open at t; expiry = INDEX open at t+H. These are not proven identical to Event Futures server entry/expiry prices. Treat as optimistic prices.

All 18 cells are scored regardless of performance; original raw source SHA256 by chunk is recorded. Source gaps are rejected per event, no interpolation, source substitutions, or post-outcome tuning. 2026 April was already inspected by predecessor lab V0.4, therefore results cannot be independent OOS or new edge proof.

Hypothetical payout sensitivity q=0.40,0.80,0.85; **never** label these actual historical Event Futures payouts. Real payouts are direction- and decision-time dependent; historical payouts are not available here. Sources failing -> SOURCE_BLOCKED, no invented PnL.

This workflow cannot activate the V0.1 model, open V0.13 forward outcomes, or merge main. Even if simulated accuracy is high, verdict remains HISTORICAL_PROXY_ONLY_NOT_EVENT_FUTURES_EDGE.
