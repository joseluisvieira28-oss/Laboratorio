# MICROSTRUCTURE SCALPING LAB — SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-25
Status: SOURCE_FEASIBLE

## Historical L2
Primary research source: Bybit BTCUSDT linear order-book archive.

Evidence:
- archive index: 1,346 consecutive daily BTCUSDT files from 2023-01-18 through 2026-09-24 at source-probe time, with no missing calendar day in the index
- raw 2023 sample: 250,000 messages, CRC PASS, zero tracked replay-integrity violations
- archive transition samples:
  - 2025-08-20 ob500: PASS_SAMPLE
  - 2025-08-21 ob200: PASS_SAMPLE
  - 2025-12-31 ob200: PASS_SAMPLE
- 2026 remains protected and unavailable to Discovery/OOS analysis

Decision: historical Bybit L2 is SOURCE_FEASIBLE for the frozen pre-holdout research program.

## Target-venue forward data
MEXC BTC_USDT public depth:
- REST snapshot reachable
- websocket subscription reachable
- 20-second sample: 6,939 incremental depth events
- zero observed internal websocket version gaps
- zero non-monotonic versions

Decision: MEXC public depth is FORWARD_FEASIBLE for prospective source replication.

## Economic gate
Current frozen MEXC API fee hurdle:
- maker: 6 bps per side
- taker: 8 bps per side
- taker/taker round trip: 16 bps before slippage

This is a severe hurdle for ultra-short scalping.

## What is NOT established
- no trading edge
- no OOS survival
- no 2026 holdout result
- no maker fill model
- no live-trading authority from this lab

Next authorized scientific stage: frozen Discovery only.
