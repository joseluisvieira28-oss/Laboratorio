# GOLD BITGET → MEXC — SOURCE GATE CLOSEOUT V0.8

Date: 2026-10-04
Run: 37193889481
Artifact SHA256: `dff8fdb0c5289cc23065a7bdc651247e17c73dbef0280a8b51a1c832452ff3dd`

## Result

`GOLD_BITGET_MEXC_SOURCE_PASS`

Frozen source checks:
- MEXC exact `XAU_USDT`: PASS
- MEXC declares `BITGET_FUTURE`: PASS
- Bitget exact `XAUUSDT`: PASS
- public 1-minute candles on both venues: PASS
- same-scale live price check under 500 bps: PASS

Probe snapshot:
- MEXC XAU_USDT: 4145.50
- Bitget XAUUSDT: 4144.54
- live dispersion: ~2.3163 bps

MEXC index origins observed:
- BINANCE_FUTURE
- BITGET_FUTURE
- BYBIT_FUTURE
- BINANCETICKER

## Governance

- outcomes opened: 0
- lead/lag tested: false
- no account/API key/private endpoint
- no wallet
- no order
- no exchange mutation
- no live-trading authorization

Historical cross-venue outcomes remain CLOSED until a separate pre-outcome rule freeze is committed.
