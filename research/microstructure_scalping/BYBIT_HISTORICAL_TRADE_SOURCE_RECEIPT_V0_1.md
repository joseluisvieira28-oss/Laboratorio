# BYBIT HISTORICAL TRADE SOURCE RECEIPT V0.1

Date: 2026-09-25
Status: PASS_SAMPLE
Workflow run: 36194037601
Scope: source gate only; no strategy outcomes.

Source:
https://public.bybit.com/trading/BTCUSDT/BTCUSDT2023-01-18.csv.gz

Observed:
- HTTP 200
- compressed bytes: 49,983,443
- decoded bytes: 171,295,863
- sample rows parsed: 1,999
- columns:
  - timestamp
  - symbol
  - side
  - size
  - price
  - tickDirection
  - trdMatchID
  - grossValue
  - homeNotional
  - foreignNotional

Timestamp sample:
1674000001.136 seconds since epoch.

Important limitation:
This historical CSV schema does NOT expose the modern public-trade cross-sequence field seq.
Therefore exact sequence-level joining between historical trades and L2 is not available from this file.

The next gate must audit timestamp alignment against L2 matching-engine cts and use a conservative fill model. No exact queue-position claim is permitted.
