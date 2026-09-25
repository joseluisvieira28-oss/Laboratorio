# CRYPTO LAB — MEXC LIVE EXECUTION V0.3 TIER-2 MICRO-LIVE — OPERATOR GUIDE

Status: PREPARED / FAIL-CLOSED / NO ORDER FROM INSTALLATION

## Policy
- governing policy: TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24
- max live notional: 10 USDT equivalent
- max total live exposure: 10 USDT
- max concurrent positions: 1
- daily realized-loss kill: 2 USDT
- rolling 7-day realized-loss kill: 5 USDT
- no martingale, averaging down, revenge sizing or automatic size escalation
- Futures, when used by a candidate mapping: isolated 1x only

## First exact candidate lane
OPTIONS-SPOTPERP-001-V2.1 LONG -> MEXC Spot BTCUSDT.

The scientific identity remains:
- CALL_IV_MINUS_PUT_IV
- positive = LONG; negative = SHORT
- V2.1 weight = min(1, expanding median RV20 / RV20)
- entry = 00:00 UTC t+1
- exit = 00:00 UTC t+2
- BASE10 / STRESS20 remain scientific reference costs

Micro-live base budget is 10 USDT and the actual LONG Spot quote order quantity is exactly:
10 USDT * frozen V2.1 weight.
It may be rounded DOWN only if a venue precision rule requires it. Never round upward to meet a venue minimum.

## Security
Use a dedicated MEXC API key with only the permissions needed for Spot account/deal read + Spot deal write.
Do not enable withdrawals or transfers.
Secrets stay in local Windows DPAPI storage. Never paste them into GitHub, Drive or ChatGPT.

## PC sequence
1. Upgrade the Radar first with the validated V0.14.4 / registry 3.7 / 8-motor package.
2. Extract this V0.3 execution bundle.
3. If needed, run windows/Set_MEXC_Preflight_Secrets.ps1 once.
4. Run windows/READY_CHECK_TIER2_MICROLIVE_V03.bat.
5. Required state: INFRA_ARMED__WAITING_CANONICAL_TIER2_SIGNAL.
6. Do not manually create an ACTIVE authority or fabricate a signal.
7. A future canonical OPTIONS LONG signal must create an immutable signal receipt and candidate-specific authority.
8. The exact quote amount is validated with MEXC POST /api/v3/order/test. That endpoint must return PASS before a real order can be transported.
9. Real transport additionally requires the local live-execution token/arming state and the exact entry window.
10. Exit guard sells only the BTC quantity acquired by that micro-live session and writes POST_TRADE_RECONCILIATION.

## Exactly-once behavior
- ORDER_INTENT is persisted before transport.
- duplicate key is consumed atomically before transport.
- if order submission times out, do NOT resubmit blindly.
- reconcile by newClientOrderId first.
- partial fill is never chased.
- restart/redeploy must reconcile active receipts before another entry.

## Current blockers that are not reasons to alter science
- a SHORT OPTIONS signal is not allowed through the Spot LONG lane.
- CED1D source FAIL_CLOSED must clear before CED can trade.
- BNB requires an exact compatible BNBBTC Spot venue.
- ETF Q4 no-peek lane remains intentionally excluded.

Installation and READY_CHECK create no order.
