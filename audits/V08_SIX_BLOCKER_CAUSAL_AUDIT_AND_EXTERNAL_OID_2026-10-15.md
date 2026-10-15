# V08 NO_LIVE_GO six-blocker audit and recovery advancement — 15 October 2026

Operator's sanitized local V08 report: authenticated MEXC Futures account GET true, flat true, HEDGE true, current SOL/BNB one-contract model true, V07 Telegram preserved, MEXC mutations zero. Six static blockers appeared in readiness receipt. **These are source-code invariant blockers, not runtime errors from the operator's Windows PC; reinstallation cannot clear them.**

## Priority and actual status

| Blocker | Status | Valid evidence required |
|--|--|--|
| ENTRY_AND_NATIVE_STOP_NOT_PROVEN_ATOMIC_ON_REAL_MEXC | UNPROVEN / VENUE-DESIGN | MEXC native stoporder/place is a separate position POST; planorder/place/v2 offers stopLossPrice but is a *conditional entry*, not a proven substitute for immediate native parent V5 entry. Venue/execution proofs, or a formally preregistered economic fork, needed. |
| BROKER_FILL_NATIVE_STOP_POST_ACK_REAL_READBACK_NOT_YET_OBSERVED | UNPROVEN / ACTUAL VENUE RECEIPT | Controlled first real experiment at an appropriate later authorized phase; position and TP/SL readbacks after broker POST ACK, same ID, volume and trigger confirmed, fault handling. No real order has been sent here. |
| FULL_NONLATCHED_TRAILING_AND_EXIT_RECOVERY_NOT_IMPLEMENTED | DESIGN RISK / NO PARITY | Pinned V5 parent source `engine/three_convex_v05/vendor/V5_PARENT_PINNED_SOURCE.py.txt`: STOP=0.04, TRAIL=0.12, ACT=0.05; after bar stop/exits, `active_stop = max(initial_stop,peak*(1-TRAIL)) if close_return>=ACT else initial_stop`. **This can *lower* the prior stop when activation lapses.** Monotonic trailing is a scientific/economic fork, not a bug fix; naive amend risks unprotected windows. Explicit freeze and independent after-cost evidence required before live. |
| REAL_POST_RISK_CONTROLLER_DIGEST_NOT_CRYPTOGRAPHICALLY_AUTHENTICATED | CODE DEFECT / LIVE BLOCK | V06 `OneUseMutationTicket` validates only a 64-hex string, **no cryptographic proof of risk-controller provenance or payload binding**; production hard-stop until independently verifiable issue/replay/account/payload/budget authority exists. |
| LIVE_CONVEX_SOURCE_PARITY_AND_PROSPECTIVE_NET_EDGE_NOT_PROVEN | SCIENTIFIC | V07 Binance public 5m → 1h/4h signals depend on parent AST functions but have not proven canonical data feed exactness, historic bar time alignment and costs. Frozen 2026 holdout must not be unlocked for post-outcome tuning. V5 parent assumes `EXPOSURE=0.95`, `FEE=0.001`, `SLIP=0.0002`. A 1-contract 10x live micro-fork differs economically; require genuinely prospective accounting and risk. |
| FIRST_REAL_ORDER_OPERATOR_AUTHORIZATION_NOT_ISSUED | AUTHORITY / INTENTIONALLY NOT REQUESTED YET | Only after controls and venue protection proven enough to define controlled first real trade; current operator asking for readiness is **not** a safe all-conditions LIVE GO. |

## New V08 development after reading operator's receipt

MEXC official documents signed private **GET** `/api/v1/private/order/external/{symbol}/{external_oid}` (“Get Order by External ID”): https://www.mexc.co/api-docs/futures/account-and-trading-endpoints/get-order-by-external-id

Implementation in **this V08 branch only**: `engine/three_convex_v06/mexc_futures_live_transport.py` allows that narrow GET for SOL/BNB and shape-bound `CL8[0-9a-f]{28}`; `get_order_by_external_oid()` checks symbol, external ID, real numeric order ID. Synthetic HTTP regression tests in `engine/three_convex_v08/test_external_oid_readback.py`. **Never interprets an absent result as safe-to-resubmit**: unknown timeout/processing state still locks ledger until reconciled.

No MEXC POST / order, no Telegram mutation, no changes to local V07/V08 Windows installation, no main merge. This improves the recovery inquiry path, but does not remove any of the six V08 constant blockers, prove a trade, or justify a new installer just to read a static NO_LIVE_GO message.

## Next meaningful gates

1. Immutable economic spec reconciliation: original V5 timing+nonlatched active-stop path vs broker mechanics, including candidate conditional entry as formally distinct path and private fees. Publish fork/NO-GO before testing any untouched outcomes.
2. Robust current private GET-only recovery for ambiguous externalOid (readbacks position, open stops, fee and symbol), nonmutation authenticated tests if available. Unknown never automatic resend.
3. Design independently verified broker-side safe-entry protection and stop amendment lifecycle, without claiming hard cap from stop model; require timeline and fault injection.
4. Independent scope-limited risk authority bound cryptographically to exact body and account, ledger, symbol, volume, leverage, budget, source and timestamp. No arbitrary digest accepted.
5. Only after full independent checks, seek explicit first-live controlled authorization; all tests must be after-cost. The existing bot sends signal observations only.

**CURRENT VERDICT: ACCOUNT_READONLY_PASS / TELEGRAM_PASS / SIX_LIVE_BLOCKERS_OPEN / EXTERNAL_OID_READONLY_RECOVERY_PATH_IMPLEMENTED_SYNTHETIC_ONLY / NO_LIVE_GO.**
