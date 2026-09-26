# BTC-CONVEX-TREND-CAPTURE-001 — V0.2 AGGRESSIVE INITIAL SNAPSHOT RECEIPT

**Authority:** PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE  
**Boundary receipt:** PROSPECTIVE_SHADOW_AUTHORITY_V0.2_RECEIPT.md

## Run

- workflow run: **35963876914**
- artifact: **10793042788**
- artifact SHA-256: **13122bc9247293fd868a500f619232d25289524c36015b4bb9c5e5d36b0b9ffe**
- snapshot time: **2026-09-24T06:20:19.946279Z**

## Boundary

- authority freeze commit: 673d50b2f786e88c593a900db1a9aac6a265d215
- freeze time: 2026-09-24T06:17:04Z
- first eligible V0.2 1h bar open: **2026-09-24T07:00:00Z**
- first eligible bar full close boundary: **2026-09-24T08:00:00Z**

The initial snapshot occurred before the first eligible V0.2 bar.

## Result

Source:
- BTCUSDT: PASS
- ETHUSDT: PASS
- SOLUSDT: PASS
- BNBUSDT: PASS
- blocked symbols: 0

Forward evidence:
- completed V0.2 bars: 0 / symbol
- signals: 0
- closed trades: 0
- pending entries: 0
- open positions: 0
- equal-weight marked return: 0
- source coverage clean: TRUE
- causal integrity blocker: FALSE

Current state:

**FORWARD_COLLECTING_ONLY**

Checkpoints:
- A / 10 trades: NOT REACHED
- B / 25 trades: NOT REACHED
- C / 50 trades: NOT REACHED

## Interpretation

This is a clean zero-state receipt.

It proves that V0.2 was initialized before its first eligible market bar and did not import pre-boundary signals/trades.

No promotion credit is created by a zero-state snapshot.
