# LIQUIDATION-PRESSURE-001 — SOURCE FEASIBILITY CLOSEOUT V0.1

Date: 2026-09-16

## Classification

**SOURCE_ACCESS_BLOCKED / REPRODUCIBLE_HISTORICAL_MARKETWIDE_LIQUIDATION_ARCHIVE_NOT_PROVEN**

This is a source/provenance classification only. It is **not** NO_EDGE, NEGATIVE_EXPECTANCY, INSUFFICIENT_SAMPLE, or any market-outcome verdict.

## Proposed mechanism

Forced-deleveraging / liquidation-pressure state in BTC derivatives, intended to test whether objectively large market-wide liquidation bursts create a prospectively defined short-horizon continuation or reversal response.

## Outcome-blind source feasibility findings

The current official Binance public-data repository documents downloadable futures aggTrades, trades and klines, but does not document a current public historical liquidation archive as part of the supported downloadable datasets.

Current Binance force-orders REST documentation available through official connector/docs is a USER_DATA endpoint for a user's own force orders, not a reproducible historical market-wide liquidation-event archive suitable for research.

Binance provides live WebSocket market streams, but live collection cannot reconstruct a historical pre-2025 Discovery corpus without introducing forward collection and sample truncation. A current/live feed is therefore not a substitute for historical point-in-time liquidation events.

## Fail-closed decision

No liquidation event population, BTC forward return, PnL, hit rate, Sharpe, continuation/reversal outcome, or strategy performance was computed.

Do not infer liquidation events from price wicks, volume spikes, taker flow or open-interest drops under this experiment ID. Those are different observables and would change the information family. Do not silently substitute third-party aggregated liquidation histories without a separately frozen vendor/source contract before outcomes.

The source-feasibility attempt is closed as **SOURCE_ACCESS_BLOCKED** under the current official/free-data-first governance.

## Firewalls

- 2025 outcome access: FALSE
- 2026 outcome access: FALSE
- BTC market outcomes opened: FALSE
- PnL computed: FALSE
- Live trading: FALSE
- Exchange mutation: FALSE
- Merge to main: FALSE
- Post-outcome tuning: FALSE

## Routing

The mechanism remains scientifically interesting but operationally blocked. A future reopening requires a prospectively pinned, reproducible historical market-wide liquidation-event source with timestamp and quantity provenance before any price outcome is opened.
