# MULTI-STABLE OPERATOR SCOUT — VERDICT 2026-10-07

Observed UTC: 2026-10-07T19:29:40.959787+00:00
Mode: PUBLIC / READ-ONLY / NO ORDERS

## BTC
- LONG BTC_USDT
- SHORT BTC_USD1
- executable normalized entry gap: 3.8683854801070563 bps
- pair round-trip fee drag on gross pair exposure: 16 bps
- fee-only full-convergence net ceiling: -14.065807259946471 bps
- 15m funding window crossed: false
- verdict: NO_TRADE_NOW

## ETH
- LONG ETH_USDT
- SHORT ETH_USD1
- executable normalized entry gap: 4.619990452145018 bps
- pair round-trip fee drag on gross pair exposure: 16 bps
- fee-only full-convergence net ceiling: -13.690004773927491 bps
- 15m funding window crossed: false
- verdict: NO_TRADE_NOW

## Operator interpretation
At the current books the dislocation is far too small to pay the four taker fills under the frozen 8 bps/fill MEXC API cost model.

A future TRADEABLE_CANDIDATE may only be surfaced when current executable books, stablecoin normalization, depth and funding-window checks produce a positive fee-only convergence ceiling.

This scout does not alter the V0.3 prospective scientific experiment and does not use sealed interim outcomes.

No trading authority.
