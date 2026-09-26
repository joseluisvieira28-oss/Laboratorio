# XVENUE-LAG-005 — SOURCE/SCHEMA GATE RESULT

Date: 2026-09-26
Workflow run: 36230840310
Status: PASS

## Binance USD-M BTCUSDT bookTicker
Observed fields include:
- b / B: best bid price / quantity
- a / A: best ask price / quantity
- E: event time
- T: transaction time
- u: update id

Public stream endpoint:
wss://fstream.binance.com/ws/btcusdt@bookTicker

## MEXC BTC_USDT
REST snapshot exposes:
- bids
- asks
- version
- timestamp
- cts

WebSocket incremental depth exposes:
- bids
- asks
- version
- cts
with message-level ts and symbol.

Observed incremental versions were consecutive in the schema sample.

Important:
An incremental update can modify a non-BBO level. Therefore raw delta price is NOT the current best quote.
The forward experiment must reconstruct the MEXC book from a REST snapshot plus a contiguous buffered delta sequence.

No authentication or trading was used.
