# LIQUIDATION-FLOW-FWD-002 — OKX SOURCE GATE PASS CLOSEOUT V0.2

Date: 2026-10-08
Verdict: `OKX_LIQUIDATION_SOURCE_PASS`
Status: SOURCE PROVEN / CALIBRATION MAY BEGIN / FAMILY NOT ACTIVE

## Canonical source run

- Workflow run: `37728295870`
- Job: `113151375661`
- Head SHA: `b1d4fc25e18d4ff2344ebbb9504d2e88c8103e2e`
- Artifact: `v013-okx-liquidation-source-v02-37728295870-1`
- Artifact id: `11529440809`
- Artifact digest: `sha256:a1c9c1e61c9a1fe169634b29da132c15ce35351ed687b2d9e5b7b7bfb608ba3b`

## Frozen gate result

600-second public OKX SWAP liquidation observation:
- subscription acknowledgement: PASS
- raw messages preserved: 123
- source errors: 0
- BTC-USDT-SWAP valid liquidation details: **1**
- ETH-USDT-SWAP valid liquidation details: **13**

Both frozen target symbols supplied at least one fresh real liquidation detail with the required
side / position side / size / bankruptcy price / timestamp fields.

Therefore the frozen source gate passes.

## Scientific boundary

This is a SOURCE PASS only.

It does NOT:
- activate the family;
- commit a numeric threshold;
- pool OKX with Bybit;
- open MEXC Event Futures outcomes;
- establish an edge.

Research outcomes opened: **0**.

## Next legitimate state

`SOURCE_PASS_PENDING_CALIBRATION`

A separate pre-calibration freeze is required before source-only threshold calibration.
No login, API key, account read, wallet, order, trading, exchange mutation or main merge occurred.
