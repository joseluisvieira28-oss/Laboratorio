# BINANCE-PREMIUM-COMPRESSION-001 — SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-18
Source gate: BPC-SOURCE-001
Canonical run: 35323511819
Canonical head SHA: 0221c74c2e6c904960ab79bd8f01125cea740817
Artifact ID: 10538785454
Artifact ZIP SHA256: 2e75780e7e9056336dae739d0590266f3b68e93ff04b024332eb6a7c17b98ae7

## FINAL CLASSIFICATION

SOURCE_DATA_PASS

## FROZEN RESULT

Official Binance Data Vision .CHECKSUM receipts only; market ZIP contents were not opened.

- symbols: BTCUSDT, ETHUSDT
- interval: 5m
- months: 2021-01 through 2024-12
- datasets:
  - USD-M premiumIndexKlines
  - USD-M perpetual klines
  - Spot klines
- expected receipts: 288
- HTTP 200 receipts: 288
- valid SHA-256 checksum lines: 288
- missing: 0
- invalid checksum lines: 0

All frozen source gates passed.

## LINEAGE

This lab is a materially different extension of the closed Spot–Perp Cash-and-Carry lineage. It does not reopen the old carry implementation. The new mechanism is short-horizon compression after an extreme intraday premium-index dislocation.

## FIREWALL

Market ZIP data opened: false
Premium values opened: false
Prices opened: false
Returns opened: false
PnL opened: false
2025/2026 accessed: false
Live trading: false
Exchange mutation: false
Merge to main: false

## RELEASE

This PASS authorizes only a separately frozen pre-Discovery protocol.
