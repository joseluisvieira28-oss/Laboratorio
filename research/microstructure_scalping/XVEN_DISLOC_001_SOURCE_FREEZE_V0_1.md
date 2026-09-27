# XVEN-DISLOC-001 — CROSS-VENUE TRANSIENT DISLOCATION
## SOURCE / FORWARD FEASIBILITY FREEZE V0.1

Date: 2026-09-26
Status: SOURCE GATE ONLY — NO OUTCOMES

## Hypothesis family
Short-lived price dislocations between a leading reference venue and the intended execution venue may create event magnitudes materially larger than single-book imbalance signals.

This source gate does NOT assert that such an edge exists.

## Why economically distinct
The observable state is a cross-venue executable-price gap, not static imbalance, microprice, liquidity depletion, or aggressive-flow confirmation alone.

## First gate
Public forward market data only.

Reference:
- Binance USD-M BTCUSDT public best-bid/ask stream

Target:
- MEXC Futures BTC_USDT public depth stream

No authentication.
No orders.
No exchange mutation.

## Required measurements
Bounded public-data capture must preserve:
- venue timestamps when available
- local receive monotonic timestamp
- best bid / best ask
- mid and spread
- executable cross-venue gaps:
  - buy MEXC ask / sell Binance bid
  - buy Binance ask / sell MEXC bid
- gap-state duration
- per-venue update age / stale flag

## Source gate
PASS_SAMPLE requires:
- both streams reachable;
- >= 1,000 valid BBO observations from each venue;
- monotonic local receive clocks;
- no crossed local BBO;
- explicit stale-data handling.

No trading labels.
No threshold selection.
No PnL claim.

Historical Discovery remains BLOCKED until a defensible synchronized historical cross-venue source is identified.
2025 OOS and 2026 protected holdout remain locked.
