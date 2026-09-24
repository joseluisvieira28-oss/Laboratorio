# L2R EXECUTION TRANSLATION FREEZE V0.1 — 2026-09-24

Status: **FROZEN BEFORE ANY NEW EXECUTION-ECONOMICS OUTCOME**  
Parent: `L2-RESILIENCY-001`  
Parent 2025 result: `VALIDATION_PASS`  
Parent evidence bundle SHA256: `e191a0f02031f8f84d264b365aeeaf4b16929dee3e4d507f034d0c3bbff06c22`

## 1. Scientific boundary

The parent result validated the weak-vs-strong replenishment mechanism in 2024 Discovery and independent 2025 holdout. It did **not** define an executable strategy and did not compute PnL, fees, spread/slippage, Profit Factor, Sharpe, leverage or position sizing.

No parent verdict is rewritten.

The original parent protocol had no privileged primary cell. The complete frozen panel remains:
- R1 -> Y5
- R1 -> Y15
- R1 -> Y60
- R5 -> Y15
- R5 -> Y60
- R15 -> Y60

Post-outcome selection of the numerically strongest 2025 cell is forbidden.

## 2. New executable identity

New LAB_ID: `L2R-EXEC-PASSIVE-001`.

This is a **new prospective execution translation**, not a retroactive claim that the parent was already tradable.

Signal hypothesis:
- same BTC Hyperliquid L2 source;
- same sweep definition, source normalization and timing;
- same RR threshold: WEAK iff RR < 1.0;
- only WEAK events are candidate continuation signals under this new identity;
- direction remains parent sweep direction: ASK-consumed => LONG continuation, BID-consumed => SHORT continuation;
- for every parent cell, signal observation/entry clock is R and evaluation/exit clock is Y;
- all six cells remain in the panel; no winner selection.

Because WEAK-only execution is being frozen after the 2024/2025 mechanism outcomes are known, any 2024/2025 execution result under this new identity is **development evidence only**, never independent confirmation. Independent execution validation must be prospective after this freeze.

## 3. Venue identity

Direct venue for the first translation: Hyperliquid BTC perpetual.

Rationale: the validated response is defined on the Hyperliquid BTC order book and midpoint. Moving execution to MEXC or another venue introduces a new cross-venue transmission hypothesis and requires a separate LAB_ID.

## 4. Taker implementation

Separate child identity: `L2R-EXEC-TAKER-001`.

At R:
- LONG enters marketably at best ask;
- SHORT enters marketably at best bid.

At Y:
- LONG exits marketably at best bid;
- SHORT exits marketably at best ask.

No leverage. No position sizing. One opportunity is evaluated independently. Any portfolio/concurrency rule requires another freeze.

## 5. Passive upper-bound implementation

`L2R-EXEC-PASSIVE-001` does **not** assume real fills.

It first runs an intentionally optimistic upper bound:
- LONG entry assumed filled passively at bid_R and exit passively at ask_Y;
- SHORT entry assumed filled passively at ask_R and exit passively at bid_Y;
- fill probability = 100% only for the mathematical upper bound;
- queue position, cancellation risk, adverse selection, latency and missed fills are ignored;
- therefore this result can only eliminate the route, never prove it executable.

If the optimistic bound fails after the frozen standard-base maker fee, the standard-base passive route closes. If it survives, only a separate prospectively frozen queue/fill-realism study is authorized.

## 6. Fee snapshot frozen for this diagnostic

Official Hyperliquid fee documentation snapshot checked 2026-09-24:
https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees

Perp fee scenarios, bps per fill:
- Maker: 0.0, 0.4, 0.8, 1.2, 1.5
- Taker: 2.4, 2.6, 2.8, 3.0, 3.5, 4.0, 4.5

Standard-base diagnostic:
- maker = 1.5 bps/fill;
- taker = 4.5 bps/fill.

These are fixed before running the new execution diagnostic. No fee reduction after outcome is permitted.

## 7. Passive panel gate

Under standard-base maker fee, the optimistic passive panel survives only if all are true:
1. equal-weight mean of the six cell net upper bounds > 0;
2. at least 4 of 6 cell net upper bounds > 0;
3. each R family (1s, 5s, 15s) contains at least one positive cell.

Otherwise:
`PASSIVE_STANDARD_BASE_UPPER_BOUND_FAIL`.

If all pass:
`PASSIVE_STANDARD_BASE_UPPER_BOUND_SURVIVES`.

Survival is not Tier 2 and is not a fill/execution pass.

## 8. Protected-data rule

The diagnostic may use only the already-open canonical 2025 corpus:
- 8,400 objects;
- 8,975,275,014 bytes;
- manifest SHA256 `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`.

2026 remains forbidden.

## 9. Firewalls

No:
- 2026 data;
- network market-data acquisition;
- orders;
- live trading;
- exchange mutation;
- wallet mutation;
- leverage;
- production sizing;
- main merge;
- cell selection after results;
- fee/cost reduction rescue;
- threshold/horizon/direction rescue.

## 10. Next routing

- Taker route: adjudicate fee-floor feasibility immediately.
- Passive route: run the frozen 2025 optimistic upper-bound diagnostic.
- Passive upper-bound FAIL => close standard-base passive route; parent mechanism remains validated.
- Passive upper-bound SURVIVES => freeze queue/fill realism before any prospective shadow.
