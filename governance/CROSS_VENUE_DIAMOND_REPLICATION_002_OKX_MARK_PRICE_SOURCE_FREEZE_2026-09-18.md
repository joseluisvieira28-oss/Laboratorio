# CROSS-VENUE-DIAMOND-REPLICATION-002 — OKX MARK-PRICE SOURCE GATE — 2026-09-18

Status: FROZEN_BEFORE_OKX_MARK_PRICE_SOURCE_ACCESS_AND_BEFORE_STAGE_B_OUTCOMES
Candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1
Venue: OKX AVAX-USDT-SWAP

## Economic requirement

The frozen Binance parent funding accounting normalizes each funding settlement cashflow using settlement mark price relative to entry price. OKX official documentation states that for USDT-margined perpetuals:

Funding fee = Position value × Funding rate
Position value = Number of contracts × Contract size × Contract multiplier × Mark price

Therefore the OKX venue replication requires historical mark price at each frozen funding settlement. Funding rate alone is insufficient for exact economic equivalence.

## Frozen source

Public unauthenticated endpoint:
GET /api/v5/market/history-mark-price-candles

Instrument:
AVAX-USDT-SWAP

Bar:
1m

Historical block:
calendar 2025 only; 2026+ forbidden.

## Stage-A mark coverage probe

Before any mark-price value, signal, return, PnL, expectancy or PF calculation:
- query timestamps around fixed anchors:
  - 2025-01-01 00:00 UTC
  - 2025-04-01 08:00 UTC
  - 2025-07-01 16:00 UTC
  - 2025-10-01 00:00 UTC
  - 2025-12-31 08:00 UTC
- persist only HTTP/provider status, timestamp count/range, exact-anchor presence, confirm flag counts if available, and timestamp fingerprints;
- do not persist o/h/l/c values.

PASS requires every anchor timestamp to be retrievable at 1m and all returned timestamps < 2026-01-01T00:00:00Z.

## Stage-B funding binding if PASS

A separate frozen execution contract must bind a funding settlement timestamp T to the mark-price candle with timestamp exactly T. If exact T is unavailable at any required settlement, the trade/source path fails closed; no nearest-price interpolation is permitted.

No live trading, orders, authenticated exchange APIs, wallets, exchange mutation, alerts/webhooks, main merge, post-outcome tuning, venue dropping or 2026+ access.
