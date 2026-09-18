# CED-1D — V3 FINAL ADJUDICATION RULE FREEZE — 2026-09-18

**Status:** FROZEN BEFORE BOOKDEPTH CAPACITY OUTCOME  
**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`

This document fixes the final V3 routing before the AVAX20 bookDepth capacity result is known.

## Immutable 2025 independent evidence

One-shot Confirmation run: `35340971526`.

Historical strict V0.2 verdicts remain immutable:
- CED1D-0031 AVAX20: `V02_CONFIRMATION_FAIL_ROBUST_TO_MARK_INTERVAL`
- CED1D-0241 SOL20: `V02_CONFIRMATION_FAIL_ROBUST_TO_MARK_INTERVAL`
- CED1D-0251 SOL60: `V02_CONFIRMATION_FAIL_ROBUST_TO_MARK_INTERVAL`

Promotion Policy V3 may only add a new re-adjudication state.

## CED1D-0241 — SOL20

Independent 2025 funded BASE economics are materially negative (~-14.91 bps/event, PF ~0.913).

Frozen V3 routing:
**TIER 4 — REJECTED**.

No rescue, direction flip, lookback change or subperiod selection is permitted.

## CED1D-0251 — SOL60

Independent 2025 funded BASE economics are materially negative (~-37.86 bps/event, PF ~0.793).

Frozen V3 routing:
**TIER 4 — REJECTED**.

No rescue is permitted.

## CED1D-0031 — AVAX20

Independent 2025 OOS:
- N = 357;
- funded BASE14 mean > 0;
- funded BASE14 PF > 1;
- funded STRESS20 mean > 0;
- concentration non-catastrophic;
- at least half of 12 major monthly blocks positive (7/12);
- no adequate independent OOS block materially destroys BASE economics.

Strict V0.2 statistical/temporal gate remains FAIL and remains disclosed.

### Final V3 route after execution-capacity gate

If the prospectively frozen bookDepth capacity receipt has:
- `status == BOOKDEPTH_CAPACITY_PASS`;
- `composite_execution_feasible == true`;
- first aggTrades economic/latency subgates remain PASS;
- first aggTrades 5-second print-fill proxy FAIL remains disclosed;
- no 2026 access;
- no signal/cost/direction/event mutation;

then the exact CED1D-0031 candidate is routed:

**TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE**

under Promotion Policy V3 Standard Replication Path via the independent-OOS branch.

This Tier 2 conclusion means:
- replicated positive edge evidence sufficient for accelerated validation;
- tiny-notional execution feasibility supported by the frozen composite evidence;
- strict V0.2 Confirmation remains historically failed;
- first aggTrades print-observability fill proxy remains a mandatory fragility;
- statistical uncertainty/temporal weakness remains a mandatory fragility;
- no claim of Tier 1;
- no production/live authorization.

If bookDepth capacity FAILS or `composite_execution_feasible == false`, AVAX20 remains:

**TIER 3 — WATCHLIST / EXECUTION UNRESOLVED**

unless a materially negative execution-economic result independently contradicts the candidate, in which case Tier 4 may apply only under the already-frozen V3 definition.

## Tier 1

No CED1D candidate may become Tier 1 in this adjudication.

Tier 1 requires a separate prospectively frozen shadow/forward operational validation and acceptable risk envelope.

## Live / production

No tier here authorizes:
- live trading;
- orders;
- exchange mutation;
- wallets;
- leverage;
- alerts/webhooks;
- production capital;
- merge to main.
