# LICP-001 — TRIGGER QUANTILE POLICY FREEZE V0.1

Date: 2026-09-26
Status: FROZEN BEFORE CALIBRATION VALUES / BEFORE OUTCOMES

This document freezes WHICH feature quantiles map into the first forward trigger.
Numeric values are not yet known and will be copied mechanically from the outcome-blind calibration receipt.

## BTC ignition
Primary source: Bybit BTCUSDT allLiquidation
Window: 5 seconds

Requirements:
- total liquidation notional >= Bybit BTCUSDT 5s burst p95
- burst side concentration >= Bybit BTCUSDT 5s side-concentration p75
- normalized pressure must be BUY or SELL, not flat

## Multi-venue confirmation
Source: Binance BTCUSDT forceOrder
Window: 5 seconds

Requirements:
- Binance BTCUSDT 5s burst notional >= Binance BTCUSDT 5s burst p75
- normalized pressure must match the Bybit BTC ignition pressure
- confirmation must become observable no later than 5 seconds after Stage 1 ignition

Binance remains confirmation-only because its public forceOrder feed is throttled.

## OI context
BTCUSDT Binance public open interest is recorded.

V0.1:
- OI is NOT a required trigger gate.
- no numeric OI threshold may be introduced after seeing propagation outcomes.

A later OI-gated version requires a new feature-only calibration and a separate pre-outcome freeze.

## ETH/SOL second wave
Source: Bybit allLiquidation
Window: 5 seconds
Maximum propagation delay after confirmed BTC ignition: 30 seconds

Requirements:
- ETHUSDT second wave: 5s burst notional >= Bybit ETHUSDT 5s p95
- SOLUSDT second wave: 5s burst notional >= Bybit SOLUSDT 5s p95
- normalized pressure must match BTC ignition pressure

No side-concentration threshold is required for ALT_SECOND_WAVE V0.1 beyond same-direction notional dominance.

## Numeric freeze rule
When calibration completes:
- copy the exact quantile values from the calibration receipt;
- do not round upward/downward based on expected signal frequency;
- if a required source-symbol quantile is unavailable because the calibration sample has no active burst bins, trigger config stays UNFROZEN and calibration must continue on new forward data;
- do not substitute Binance values for missing Bybit values or vice versa.

## Outcome isolation
No MEXC post-trigger price outcome may be opened before all required numeric thresholds exist and the trigger config status is explicitly changed to FROZEN.
