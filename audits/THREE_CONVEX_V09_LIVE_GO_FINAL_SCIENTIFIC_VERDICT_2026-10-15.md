# CRYPTO LAB THREE CONVEX V09 — SCIENTIFIC + OPERATIONAL LIVE-GO VERDICT
Date: 2026-10-15 UTC. Scope: FUTURES-only SOL_CONVEX_NATIVE_5M, SOL_CONVEX_1H, BNB_CONVEX_4H, 1 MEXC minimum contract/order, isolated 10x, existing Windows V07 Telegram.

## Executive signed-off *research* verdict

**REAL AUTOMATIC LIVE GO: NO-GO (as of 2026-10-15).**

This is not a verdict that CONVEX has no possible edge; it is an evidence-based **deployment prohibition for this exact MEXC implementation today**. Do not place, arm, enable, or merge any trading task. Continue only work on unproven broker safety and truly prospective scientific validity. No real MEXC POST was executed in this review.

## What is actually real today (from operator-supplied local receipts)

- MEXC Futures private authenticated GET succeeded, USDT balance/availability read; HEDGE enabled; at observation time flat with no positions, orders or stops. Real SOL and BNB public contract data: 0.1 SOL, 0.01 BNB one contract, 10x nominal margin model allowed, and conservative 8bp taker-side fee model. A snapshot **does not establish** that an actual 10x isolated position is configured, nor that an entry could be protected.
- For the operator's snapshot on 2026-10-15T08:16:33Z, estimated 1-contract stop-event loss including fixed modeled slippage/fee/funding: SOL 0.43627509316 USDT, BNB 0.30673426714 USDT; sum ~0.74300936 USDT, not a hard limit. Initial model margins ~1.02760548 + 0.72104418 = 1.74864966 USDT. Broker actual available balance was > these margins at snapshot time; does **not** guarantee free margin or order acceptance on next signal.
- Windows V07 Telegram actually delivered operator's `CRYPTO LAB V07 ALERTAS LIGADOS` test; V07 `TAREFA_V07: Running`, authenticated MEXC GET and live public Binance 5m source TRUE. This proves monitoring connectivity, not executing orders or receiving an actual CONVEX entry signal.

## Why historical income does not authorize one-lot 10x

Pinned parent V5 source SHA `19c8b8e2363f253458db42111b6701f3a3ef1f4b`, frozen at `engine/three_convex_v05/vendor/V5_PARENT_PINNED_SOURCE.py.txt`, used `EXPOSURE=0.95`, `FEE=0.001`, `SLIP=0.0002` in historical simulation. Current execution policy is *one minimum physical contract per symbol, and only two physical LONG symbols* (SOL5m and SOL1h cannot have independent same-side positions under the account's HEDGE), conservative modeled fees 0.0008/side and slippage 0.0002/side, plus uncertain funding and venue basis. Thus the purported original 2023–25 +59.9%/+59.4%/+27.4% historical returns cannot be transposed to this fork. A per-contract proportional PnL edge might still exist, but no independent venue-specific 2026 prospective closed trade series is available. **Positive expectancy is unproven, not disproven.**

For 2026-10-15 1-lot example, taker+slippage 8+2 bp per side =20bp round trip, plus a modeled 5bp funding reserve = ~25 bp of notionals: ~0.0257 USDT SOL at 10.274 USDT notional and ~0.0180 USDT BNB at 7.209 USDT notional, before any extra spread/impact/uncertain funding or forced liquidation. Fees are cents, not inherently insurmountable; the problem is absent *forward profit after costs* data.

V09 `economic_gate.py` freezes an **initial prospective statistical SCREEN**, earliest UTC 2026-10-16 00:00Z (after V09 source publication). By design it cannot produce LIVE GO from an unverified user-authored file: independent exchange receipts required, ≥60 days, ≥90 closed trades, ≥20 per lane, actual fees+funding+fills, positive conservative lower bound; passing returns `CONDITIONAL_ECONOMIC_SCREEN_ONLY` and cannot independently authorize orders. Screening does not correct all serial correlation or selection bias; after-cost shadow vs real live cannot be silently conflated. The 2026 protected historical holdout is untouched.

## Venue proof blockers

**MEXC new official documentation:**
- `POST /api/v1/private/stoporder/place` position-linked protective stop is a separate mutation, and explicitly says repeated same-price pending TP/SL may ACK while quantity updates asynchronously. Therefore stop POST ACK != native protected quantity. Requires authenticated `GET /api/v1/private/stoporder/list/orders` later, matching exact position, volume, state and price.
- `POST /api/v1/private/planorder/place/v2` supports `stopLossPrice` in an order with **mandatory triggerPrice and triggerType**; this is a conditional plan order, NOT proven equivalent to a strictly scheduled V5 market entry.
- Older MEXC GitHub API docs show `stopLossPrice` on a legacy `POST /api/v1/private/order/submit` market request, but mark that interface **under maintenance**. V06's current `POST /api/v1/private/order/create` does not include `stopLossPrice` and the corresponding immediate protective atomicity has NOT been documented/observed for this account. Do not infer that legacy behavior works on current endpoint. Need official current account/venue-confirmed protected market entry flow, and real order+position+native stop readbacks *under a controlled, separately authorized pilot*.
- Binance OHLC stop checks are not automatically equivalent to a MEXC fair/mark-price native trigger, including gaps/basis and funding/liquidation. No source/venue parity proof.

## Source-frozen ORIGINAL trailing blocker

Historical V5 nonlatched rule is strictly `active_stop = max(initial_stop,peak*(1-.12)) if completed_own_tf_close_return>=.05 else initial_stop`, stop first then update after own completed TF. Example actual entry 100, peak 114, completed close 110: target stop 100.32. Subsequent completed close 104 while previous broker stop 100.32: target **96.00**, a true WEAKEN requiring replacement/amend on live MEXC. A no-weakening trailing is a different strategy/economic fork and is **not** silently substituted. V09 `trailing_gate.py` computes tick-floored target and explicitly refuses any broker amendment until atomic/reviewed native-stop lifecycle is proven.

## Operational risk-controller authentication blocker

V06 `OneUseMutationTicket.risk_controller_digest` accepts a 64-character hex *shape*; it does NOT authenticate an independent permit. This remains a serious direct-write vulnerability of the old library interface if treated as production authority. V09 `authority_gate.py` establishes detached Ed25519 verification of source lane+symbol, 1 contract, 10x isolated HEDGE long, immutable canonical order SHA-256, deterministic externalOid bound to exact source lane:signal-close identifier, account receipt SHA-256, short TTL, 0.50 USDT modeled risk ceiling and SQLite on-disk one-use nonce consumed before any possible network write. A test-only signing key is generated only by tests. **Still not integrated into V06 write transport, private signing key issuance/protection and independent account risk-controller are not built or reviewed; V09 return value expressly states `actual_live_order_authorization: false`.** No GO.

## Tests and repository proof

Draft PR [#233](https://github.com/joseluisvieira28-oss/Laboratorio/pull/233) on V08. GitHub Actions [#38726863977](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38726863977): **203 tests PASS on Windows and Ubuntu** (30 new V09, 26 V08, 22 V07, 75 V06, 50 V05). Tests are mocks/invariant verifications, **zero live fills**, no protected holdout opening, no exchange mutation, V07 task and main unchanged.

## Exact current six-blocker classification

1. **ENTRY_AND_NATIVE_STOP_NOT_PROVEN_ATOMIC_ON_REAL_MEXC — OPEN/CRITICAL**: no documented verified atomic immediate protected market order under active V06 endpoint.
2. **BROKER_FILL_NATIVE_STOP_POST_ACK_REAL_READBACK_NOT_YET_OBSERVED — OPEN/CRITICAL**: cannot be resolved from Python mocks or API GET of a flat account; needs tightly supervised exchange proof once feasible.
3. **FULL_NONLATCHED_TRAILING_AND_EXIT_RECOVERY_NOT_IMPLEMENTED — OPEN/PARTIAL**: exact stop geometry/WEAKEN detection implemented; tested broker amend/cancel/close, crash recovery, external broker custody and runbook missing.
4. **REAL_POST_RISK_CONTROLLER_DIGEST_NOT_CRYPTOGRAPHICALLY_AUTHENTICATED — OPEN/PARTIAL**: verified independent-issuer crypto primitive implemented in V09, but no safe authority issuance nor enforced broker transport integration.
5. **LIVE_CONVEX_SOURCE_PARITY_AND_PROSPECTIVE_NET_EDGE_NOT_PROVEN — OPEN/CRITICAL**: V07 public source GET operational and V5 AST pinned; full canonical RSI/TF historical parity and net 1lot forward positive signal outcome not validated.
6. **FIRST_REAL_ORDER_OPERATOR_AUTHORIZATION_NOT_ISSUED — NOT AUTOMATIC**: user wants eventual LIVE GO but zero proof for protective entry. Before any controlled venue test, must present actual bounded protocol including max loss not guaranteed, recheck account/positions/stops, and obtain scope-limited explicit activation; initial development consent is not proof of protection.

### Decision and operator instructions

**No installer to run.** Preserve existing working V07 Telegram and V08 readiness. Do not activate Futures operator, open first test position, restart old V03 tasks, merge branch or reveal API secrets. There is no honest engineering shortcut to prospective outcome evidence, nor does a static FAIL become PASS through a script. The only truthful deployable state now is `NO_LIVE_GO`.

Next authorization-changing evidence needed: venue-level documented immediate attached stop with actual per-fill readback and robust failure management; independent secured risk signing enforcement; verified nonlatched stop lifecycle and crash recovery; untouched prospective Binance/MEXC costed signal forward after 2026-10-16 freeze. Reassess only on **new evidence**, not time elapsed alone.

**FINAL regression**: GitHub Actions [38726863977](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38726863977), both OS PASS, 203 tests per platform. Two further tests verify that a valid signed permit cannot be moved to a different V5 close or order OID. No issuance service, real order, wallet or MEXC mutation was added. V09 remains NO_LIVE_GO.
