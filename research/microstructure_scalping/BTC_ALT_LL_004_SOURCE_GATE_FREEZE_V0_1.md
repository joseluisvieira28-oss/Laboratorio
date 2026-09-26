# BTC-ALT-LL-004 — MICRO LEAD-LAG SOURCE GATE FREEZE V0.1

Date: 2026-09-26
Status: SOURCE GATE ONLY

## Economic hypothesis
An observable BTC microstructure shock may lead a larger short-horizon move in a follower perpetual such as ETHUSDT or SOLUSDT.

This is distinct from H180-0001:
- H180-0001 studied hourly lead-lag.
- BTC-ALT-LL-004 is a sub-minute / minute microstructure hypothesis.
- No H180 parameters, outcomes or thresholds are reused.

## First source target
Fresh Discovery date:
2024-05-01

Required public historical sources:
- BTCUSDT L2 + trades
- ETHUSDT L2 + trades
- SOLUSDT L2 + trades

All must be available before any outcome protocol is frozen.

## Hard boundaries
- 2025 OOS remains locked.
- 2026 protected holdout remains locked.
- No cross-asset outcome test until source gate PASS.
- No substitution of candles for executable BBO without explicit protocol change.
