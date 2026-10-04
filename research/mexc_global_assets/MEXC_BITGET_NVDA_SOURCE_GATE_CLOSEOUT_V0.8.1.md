# MEXC ↔ BITGET NVIDIA — SOURCE GATE CLOSEOUT V0.8.1

Date: 2026-10-04
Run: 37195466027
Artifact SHA256: `1934da2f17fe825d1e24b262891b95047f2c30efd484874fbb0d970204ca0f3b`

## Verdict

`MEXC_BITGET_NVDA_SOURCE_PASS`

## Identity evidence

MEXC:
- exact contract: `NVIDIA_USDT`
- `apiAllowed=true`
- contract size: 0.01 NVDA
- public `indexOrigin` includes:
  - `BINANCE_FUTURE`
  - `BITGET_FUTURE`
  - `BINANCETICKER`
  - `PYTH`
  - `KAIKO`

Bitget:
- exact symbol: `NVDAUSDT`
- base coin: `NVDA`
- quote coin: `USDT`
- symbol type: perpetual
- status: normal
- `isRwa=YES`
- public maker fee metadata: 0.0002
- public taker fee metadata: 0.0006
- minimum trade: 5 USDT

## Live source snapshot

MEXC:
- index: 234.76
- ticker bid/ask: 234.92 / 234.93

Bitget:
- bid/ask: 234.94 / 234.95
- mid: 234.945

MEXC index vs Bitget mid:
- approximately -7.8742 bps

Both venues exposed public/no-auth 1-minute candle data.

## Governance

- historical outcomes opened: 0
- lead/lag tested: false
- auth used: false
- account reads: false
- wallets: false
- orders: false
- exchange mutation: false
- live trading authorized: false

## Prior-history contamination firewall

Existing Event Futures research inspected NVIDIA-linked outcomes over April–July 2026 discovery periods.
The Global Asset index-basis discovery also inspected NVIDIA over June–July 2026.

The prior freezes explicitly kept September 2026 locked/not fetched for NVIDIA-linked Event Futures work, and the Global Asset index-basis run stopped before September.

Therefore any new retrospective NVIDIA research must exclude April–August and may use September only under a fresh pre-outcome freeze.

This source PASS does not authorize outcome access by itself.
