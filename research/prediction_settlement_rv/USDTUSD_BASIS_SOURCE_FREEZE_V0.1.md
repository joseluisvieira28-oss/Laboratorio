# PREDICTION-SETTLEMENT-RV-001 — USDT/USD BASIS SOURCE FREEZE V0.1

Date: 2026-09-27
Status: FROZEN_SOURCE_ROUTE / OUTCOME_BLIND
Lab: PREDICTION-SETTLEMENT-RV-001

## Purpose

Freeze a public, causal USDT/USD observation route before any settlement-basis economics are inspected.

## Source

Provider:
Coinbase Exchange

Product:
USDT-USD

Public endpoint:
https://api.exchange.coinbase.com/products/USDT-USD/ticker

## Source-readiness proof

Run:
36339649202

Artifact:
10938113181

Observed schema keys:
- ask
- bid
- price
- rfq_volume
- size
- time
- trade_id
- volume

Required source fields present:
bid = YES
ask = YES
time = YES

Raw response SHA256 at source probe:
bcb48e8fb5dea56f6e1ed511c81207881c94ce6a9a8aebf51f1cbf93a9c27aaa

The source probe deliberately did not persist or expose the bid/ask values.

## Frozen later-use rule

If a later economic protocol is authorized, the primary causal USDT/USD basis observation shall be derived from the contemporaneous Coinbase Exchange USDT-USD public best bid/ask snapshot captured inside the same synchronized observation batch as the two prediction-market legs.

The exact transform is NOT authorized yet and must be frozen in the later economic protocol.

No historical nearest-neighbor fill.
No future quote.
No silent imputation.
No provider substitution after outcomes.

## Failure rule

Missing bid, ask or provider timestamp; request failure; stale timestamp; schema change; or synchronization failure makes that observation source-invalid.

This source freeze authorizes acquisition only. It does not authorize economic analysis.
