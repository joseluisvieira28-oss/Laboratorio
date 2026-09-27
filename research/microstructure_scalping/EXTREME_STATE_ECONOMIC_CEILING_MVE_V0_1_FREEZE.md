# EXTREME-STATE ECONOMIC CEILING MVE V0.1 — PRE-RUN FREEZE

Date: 2026-09-25
Phase: DISCOVERY ONLY
OOS 2025: LOCKED
HOLDOUT 2026: LOCKED

## Purpose
Before spending effort on queue/fill simulation, test whether extreme L2 states can even clear transaction fees under unrealistically favorable maker assumptions.

This is an ECONOMIC CEILING test, not a backtest.

## Source
Same frozen Discovery source:
- Bybit BTCUSDT
- 2023-01-18
- first 250,000 L2 messages
- 1-second anchors

This source has already been used for Discovery and is NOT treated as OOS.

## Features
- abs(microprice_displacement_bps)
- abs(imbalance_l1)
- abs(imbalance_l5)
- abs(imbalance_l10)

Direction remains sign(feature).

## Generic magnitude buckets
Thresholds are empirical feature-magnitude percentiles:
50%, 75%, 90%, 95%, 99%.

These are generic monotonic buckets, not outcome-optimized numeric thresholds.

## Horizons
5s, 15s, 30s.

## Optimistic execution ceilings

### Maker entry + taker exit
Assume immediate maker entry fill at current best quote with zero queue penalty.
Exit crosses future BBO.
Fees:
- Bybit reference: 7.5 bps round trip
- MEXC API: 14 bps round trip

### Maker entry + maker exit — optimistic upper bound
Assume immediate maker entry AND maker exit fills at current/future best quotes with zero adverse selection and zero queue penalty.
Fees:
- Bybit reference: 4 bps round trip
- MEXC API: 12 bps round trip

No slippage is charged in this ceiling test. This deliberately favors survival.

## Kill criterion for MEXC
If every tested feature × bucket × horizon with n>=100 has mean MEXC maker-maker net <= 0 even under the optimistic upper bound, classify:
MEXC_MAKER_ECONOMIC_CEILING_FAIL_SAMPLE

If any combination exceeds zero:
CEILING_SURVIVOR_EXISTS
and only then proceed to conservative queue/fill simulation.

No candidate is promoted from this MVE.
