# LIQUIDATION-FLOW-FWD-001 — ETH MARKET LIVENESS DIAGNOSTIC CLOSEOUT V0.13.1

Date: 2026-10-03
Status: DIAGNOSTIC ONLY / NO LIQUIDATION GATE CREDIT
Verdict: `ETH_MARKET_LIVE`

## Run

- workflow: `MEXC V0.13.1 Bybit ETH Market Liveness Diagnostic`
- run: `37100470880`
- job: `111138832989`
- head: `76bfc9e97f97501430987339cd773a3e7b4b97bc`
- artifact: `v0131-bybit-eth-market-liveness`
- artifact id: `11265744056`
- artifact digest: `sha256:e5f2c243a0ad62f4934b1fcc2c79dfa9ce9e34568089c817af71f38603d00e0a`

## Result

On the same Bybit production linear public websocket used by the liquidation family:

- subscription acknowledged;
- 25 `tickers.ETHUSDT` messages observed;
- 1 `publicTrade.ETHUSDT` message observed;
- errors: 0;
- research outcomes opened: 0.

This proves the ETHUSDT public market feed was live and active during the diagnostic.

It does NOT satisfy the liquidation source gate and contributes zero calibration observations.

Combined with the independent successful acknowledgement of `allLiquidation.ETHUSDT`, the current missing piece is specifically a real ETH liquidation payload, not evidence that ETHUSDT itself or the public websocket was inactive.
