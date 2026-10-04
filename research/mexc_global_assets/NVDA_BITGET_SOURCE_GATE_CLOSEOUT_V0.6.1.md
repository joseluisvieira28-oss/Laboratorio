# NVDA BITGET → MEXC — SOURCE GATE CLOSEOUT V0.6.1

Date: 2026-10-04
Run: 37193539908
Artifact SHA256: `01be3b630bf3d23eb096949c770f7e5b841ba8f44d99f83406d3ff1c77b057a0`

## Result

`NVDA_BITGET_MEXC_SOURCE_PASS`

All frozen checks passed:
- MEXC identity: PASS
- MEXC declares `BITGET_FUTURE`: PASS
- Bitget `NVDAUSDT` identity: PASS
- public 1m candles on both venues: PASS
- live same-scale check < 500 bps: PASS

Probe snapshot:
- MEXC NVIDIA: 234.84
- Bitget NVDAUSDT: 234.85
- dispersion: ~0.4258 bps

## Runtime notes

- Binance NVDAUSDT is documented publicly, but the GitHub-hosted runner received HTTP 451 from Binance Futures due runner location.
- Pyth was excluded because current Hermes access requires an API key.

Neither limitation affects the narrower Bitget→MEXC source binding because MEXC independently declares Bitget Futures as an index origin.

## Governance

- outcomes opened: 0
- lead/lag tested: false
- no accounts/API keys/private endpoints/wallets/orders/mutation
- no live trading authorization

A separate pre-outcome freeze is required before any historical return scoring.
