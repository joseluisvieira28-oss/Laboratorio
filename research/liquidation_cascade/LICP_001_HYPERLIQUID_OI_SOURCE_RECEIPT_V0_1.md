# LICP-001 — HYPERLIQUID OPEN-INTEREST SOURCE RECEIPT V0.1

Date: 2026-09-26
Workflow run: 36231577911
Status: PASS_SAMPLE

Public endpoint:
- POST https://api.hyperliquid.xyz/info
- type: metaAndAssetCtxs

Observed assets:
- BTC openInterest present
- ETH openInterest present
- SOL openInterest present

The endpoint also returned current mark price, but price is not used by the LICP trigger calibration.

Decision:
Hyperliquid provides a public, unauthenticated open-interest context source for BTC/ETH/SOL.

V0.1 use:
- approximately 5-second forward polling
- contextual deleveraging evidence only
- not a trigger gate

This replaces the Binance OI REST path that was inaccessible from the GitHub runner.
