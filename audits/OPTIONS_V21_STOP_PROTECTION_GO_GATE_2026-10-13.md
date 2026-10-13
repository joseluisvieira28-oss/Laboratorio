# OPTIONS V2.1 — stop protection and live GO audit (2026-10-13)

Status: **ENGINEERING BUILD PASS / LIVE TRADING NO-GO**

## Traceability
- Branch: fix/options-v21-protective-stop-recovery-2026-10-13
- Draft PR: https://github.com/joseluisvieira28-oss/Laboratorio/pull/200
- Windows CI: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38383924279 — completed success, mock-only/CI.
- Parent safety PR: https://github.com/joseluisvieira28-oss/Laboratorio/pull/199
- No main merge, no exchange mutation, no private API/account read, no local deployment by this audit.

## Safety changes implemented (engineering-only)
1. New opening MARKET orders are rejected before mutation transport without an explicitly supplied valid broker-side stopLossPrice. Futures BTC_USDT only, fixed 1x ISOLATED and existing 10 USDT maximum notional.
2. Engine gate requires a new, distinct, prospective protective stop policy ID and immutable signal stop price, LONG/SHORT direction, maximum 200 bps price-distance safety envelope, tick alignment, and current MEXC contract metadata.
3. After a fill, require an exchange-side active TP/SL order receipt that matches position ID, direction, volume and price; on failure, existing emergency close path is invoked. Existing entry-intent recovery cannot declare recovery without such proof and never resends an uncertain entry blindly.
4. Active-trade heartbeat checks position ID and matching active broker stop; missing position requires reconciliation rather than another exit.
5. Unreadable local active/P&L receipts are fatal, not interpreted as flat or zero loss. Orphan BTC stop orders block new entries.
6. Added synthetic mocks/tests for broker-stop verification, corrupt receipts, LONG/SHORT stop payload and naked-order rejection.

## Critical GO blockers — NOT RESOLVED
- **Protection semantics still unproven in live MEXC**: docs list stopLossPrice and TP/SL order query endpoints, but there is no exchange-accepted, separately authorized empirical proof of the exact opening-order stop and subsequent stop-order status/trigger behavior. No live testing in this audit.
- **No frozen stop-protected signal**: the canonical V2.1 execution signal currently does NOT emit protective_stop_policy_id or protective_stop_loss_price. The new branch intentionally cannot open a position even if operator ARMED receipt were present.
- **Scientific fork**: forced exits via stop change the economics and return distribution; no right to substitute historical spot-parent OOS results as evidence for this new execution fork. Freeze policy BEFORE untouched forward outcomes; evaluate prospectively.
- **Negative taker route economics**: Frozen V2.1 execution economics dated 2026-09-28 show 2025 independent OOS NET10 mean +5.0427663334 bps and NET20 -4.6759378383 bps. Cost sensitivity to 16bps full-notional is -0.7884561696 bps/opportunity before spread, slippage or funding. Official MEXC API Futures June 2026 announced 8bps taker/fill and 6bps maker/fill; the current MARKET/MARKET route is not defensibly profitable after costs. Sources: governance/OPTIONS_SPOTPERP_001_V21_EXECUTION_ECONOMICS_TRUTH_GATE_V0.1.md, https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742
- **Emergency exit failure is not a guaranteed loss cap**; slippage/gaps/liquidation, position closure while host offline, stop API timeouts and closed-position reconciliation require stronger proof.
- **Shared exchange account**: non-OPTIONS operators may open positions; global account/position, stop, and risk preflights must remain fail-closed.
- CI PASS is compilation/mocks, NOT on-exchange execution proof, realized net profitability, nor order-placement authority.

## Decision
- Engineering branch: **TEST BUILD GO**, **PRODUCTION NO-GO**.
- Windows operator: retain existing OPTIONS V2.1 task **Disabled**, no ARMED receipt, and do not execute installer, launcher, or private authenticated preflights.
- Prospective work: independent stop-policy freeze and untouched shadow outcomes; offline restart/partial-fill/stop-trigger fault injection, reconciliation receipts; independent fee/funding/slippage proof and sufficient statistically meaningful positive net edge; broker-safe remote stop proof under separate authorized micro-live gate only after research establishes defensible expectancy.
- Never claim 8/8 loaded radar means 8/8 ready to trade.
