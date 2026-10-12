# BTC-CONVEX trailing ETH/SOL/BNB — execution bridge engineering receipt — 2026-10-12

**NOT LIVE. NO ORDER TRANSPORT CERTIFIED. NO RUNTIME DEPLOYMENT.**

## Concrete local engineering (new candidate only)
Prepared a separate source-code package `ConvexRadar_MEXC_Execution_Bridge_V01_NO_LIVE.zip` with:
- `convex_core.py`: frozen long-only trailing formula, 4% initial stop, confirmed-close 5% activation, 12% peak offset, no fixed TP, and separate stop/risk contract sizing. One open long per symbol, max three assets.
- `mexc_futures.py`: authenticated, host/path-allowlisted MEXC Futures request encoder with isolated market long order, bounded 1–20x leverage, position-level stop-only, and stop-revision paths. Requests are injectable/mocked; no real requests or account credentials were supplied.
- `supervisor.py`: local prospective signal evidence identity ingestion, fail-closed account/position ownership state, explicit compile-time `PRODUCTION_ORDER_TRANSPORT_CERTIFIED=False`. **Not a working live trade dispatcher.**
- `test_bridge.py`: 17 unit tests pass locally; mocks validate request shapes; **no signed real request, actual filled trade, or live stop update has been tested**.

SHA256 of ZIP: `f6ae50589d4f935c9796ec5aa39fcbe86d33d982b0ed7f0fe5c2be30d5c343f6`. Uploaded to operator Google Drive, Drive ID `1oFJ5DujheiZ8yQ1XMdU4gfrJZj1mIzgA` (private). This research package is NOT a Windows live installer or an additive live slot.

## Official documented API semantics (as inspected on 2026-10-12)
- `POST /api/v1/private/stoporder/place`: permits stop-loss with no take-profit (one of SL/TP must be nonzero): https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/place-tpsl-order-by-position
- `POST /api/v1/private/stoporder/change_plan_price`: source described in legacy published API, not authenticated on current account; must confirm an existing position-based stop ID can be updated and read back before live use.
- `POST /api/v1/private/order/create` and `/position/change_leverage`: separate mutation surface.
- The old operator V0.4 transport `required_leverage in {1,5}` and `place_position_tpsl` requires BOTH stopLossPrice and takeProfitPrice, so plugging this candidate into old executor without an adapter **will change the scientific exit rule** and is forbidden.

## Critical end-to-end blockers (NO LIVE GO)
1. Existing V0.3/V0.4 Windows executor, account positions/orders/SL and canonical Radar single-owner identity must be reconciled *read-only*. No unsafe switching/stopping of old position manager.
2. Attach initial stop to filled new position and verify exchange-side coverage of exact positionId/vol from *actual MEXC authenticated responses*. Must prove fail-safe handling of partial fills, order response timeouts/unknown, restarts, orphan positions and stop rejection. No real trades have been issued here.
3. Position-level stop revision: prove authenticated modification and read-back, including stop loosening when confirmed-close PnL falls below 5% (original NONLATCHED behavior) and broker rules for stop above current market after an extreme candle. The latter may diverge from the historical OHLC close-to-next-open model.
4. Live risk/lot/equity/margin/leverage 20x and liquidation distance are NOT the same as nominal replay risk, and minimum ETH lot can exceed allowed stop-risk. Never increase size merely to clear lot floor.
5. Build and validate a real Windows installation/handover package plus 24x7 source scheduler and journal, then issue a separately hash-bound active authority and verify local run. The existing standalone observer is NOT integrated into production.

Operator asked for live automation, and goal is preserved; this document DOES NOT falsely claim completion or solicit extra research/backtest. Prior 17 tests are engineering regressions, not economic validation.

No main merge, no exchange mutation, no account read, no open 2026 holdout, no existing position altered.
