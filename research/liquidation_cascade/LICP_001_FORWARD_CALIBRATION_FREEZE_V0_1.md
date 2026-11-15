# LICP-001 — FORWARD CALIBRATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN BEFORE POST-TRIGGER OUTCOMES

## Purpose

Estimate only the distribution of observable forced-liquidation pressure and feed health.
This phase MUST NOT inspect future returns after candidate triggers.

## Calibration universe

Public streams only:
- Bybit allLiquidation: BTCUSDT, ETHUSDT, SOLUSDT.
- Binance USD-M all-market forceOrder snapshots: BTCUSDT, ETHUSDT, SOLUSDT.
- MEXC BTC_USDT incremental depth for source-health / target-market availability only.

Bybit and Binance are never pooled as if their liquidation-volume semantics were identical.
Bybit is the primary liquidation sensor because its official allLiquidation topic is intended to push all liquidations.
Binance is a corroborating sensor because its forceOrder stream is throttled to the latest liquidation order per symbol per 1,000 ms interval.

## Outcome blindness

During calibration, persist:
- source event timestamp;
- local monotonic receive timestamp;
- venue;
- symbol;
- liquidated side;
- size;
- bankruptcy / reported execution price;
- event notional where definable;
- rolling liquidation notional/count summaries.

Do NOT persist or compute:
- forward return after a liquidation burst;
- MFE / MAE;
- direction accuracy;
- PnL;
- Sharpe;
- post-trigger spread change;
- any label derived from future price.

MEXC depth is used in this phase only to prove continuous target-source health. It is not joined to liquidation events for outcome analysis.

## Fixed calibration windows

Aggregate liquidation pressure separately by venue and symbol over:
- 500 ms
- 1 s
- 5 s
- 15 s
- 60 s

## Candidate trigger family to freeze after calibration

For Bybit only, compute rolling notional percentile ranks using past-only observations.
Candidate severity tiers will be selected mechanically from:
- P95
- P99
- P99.5
- P99.9

No percentile may be promoted or rejected using future returns.

Cross-venue confirmation is a separate binary feature:
- Binance same-direction forced-liquidation snapshot observed inside ±2 s of the Bybit burst.

Because Binance is throttled, absence of a Binance event is NOT proof of absence of liquidation pressure.

## Minimum calibration evidence before trigger freeze

Before opening any price outcome:
- >= 7 UTC days of forward collection;
- >= 250 Bybit liquidation messages across the three symbols;
- >= 50 BTCUSDT Bybit liquidation messages;
- >= 95% collector uptime over scheduled observation time;
- zero unexplained local monotonic clock regressions;
- raw append-only event log hash recorded;
- reconnect gaps explicitly logged.

If the event-count criteria are not met after 7 days, calibration continues until they are met. No threshold relaxation is permitted.

## Post-calibration trigger freeze rule

After the minimum evidence is met:
1. calculate past-only distributions;
2. write exact notional thresholds for each symbol/window/tier;
3. select at most ONE primary severity tier and ONE robustness tier using event-frequency / operational feasibility only;
4. freeze them in a new pre-outcome document;
5. start a NEW forward outcome epoch strictly after the freeze timestamp.

Calibration events can never become outcome observations.

## Later outcome epoch — not yet open

Candidate horizons reserved for the later freeze:
- 1 s
- 2 s
- 5 s
- 15 s
- 30 s
- 60 s

Executable economics and direction rules must be frozen before those outcomes are inspected.

No live trading authority is created by this document.
