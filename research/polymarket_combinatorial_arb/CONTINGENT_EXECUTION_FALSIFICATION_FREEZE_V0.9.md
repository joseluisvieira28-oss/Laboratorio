# POLY-COMBINATORIAL-ARB-001 — CONTINGENT EXECUTION FALSIFICATION FREEZE V0.9

Date: 2026-09-27
Status: FROZEN_BEFORE_V0.8_OUTCOME / CONTINGENT / NOT AUTHORIZED TO RUN YET

## Activation condition
V0.9 may run only if the already-running V0.8 independently closes as:
PROSPECTIVE_BOOK_EXECUTABLE_SIGNAL_OBSERVED.

If V0.8 closes with any other adjudication, V0.9 remains dormant.

V0.8 snapshots may not be reused as V0.9 evidence.

## Purpose
Attack any future V0.8-positive book signal for persistence and non-atomic multi-leg execution fragility without placing orders.

## Unchanged economics
- same frozen events;
- BUY_ALL_YES only;
- q=10;
- same first-party fee formula/descriptors;
- same 0.05 BASE / 0.10 STRESS package buffers;
- public unauthenticated CLOB only.

## Test A — persistence
For each new post-V0.9 signal episode:
- T0 qualifies only when stress_margin > 0 under the frozen V0.8 rule;
- reacquire complete current-book batches at T+250ms, T+500ms and T+1000ms;
- the episode survives persistence only if the unchanged q=10 stress_margin remains >0 at all three confirmation points.

No missed point may be backfilled.

## Test B — deterministic sequential-fill latency proxy
Condition IDs are ordered lexicographically before any V0.9 outcome.

At a new signal episode:
- leg 1 uses a fresh book state at T0;
- leg i uses a fresh current-book batch targeted at T0 + (i-1)*100ms;
- only the specific leg i ask-depth is consumed from that scheduled batch;
- fee formula remains unchanged;
- package cost is the sum across these time-staggered leg observations;
- if any leg is unfillable or transport-late, the episode fails the sequential proxy;
- sequential stress margin must remain >0 after the inherited 0.10 package buffer.

This is deliberately adverse to the instantaneous batch signal and approximates non-atomic execution drift. It is not a claim of real fill.

## Minimum evidence
At least 20 independent signal episodes separated by >=60 seconds.
At least 2 distinct frozen events must contribute signal episodes.

No artificial extension if the signal is rare.

## Falsification
A candidate can progress beyond book-signal status only if:
- >=50% of eligible episodes survive the 1-second persistence ladder;
- >=50% survive the deterministic sequential-latency proxy;
- both represented events have at least one survivor;
- no single episode contributes >25% of aggregate positive sequential stress margin.

These thresholds are frozen before V0.8 outcome inspection.

## Governance
No orders, auth, wallet, capital or live trading.
No parameter rescue after V0.8/V0.9 outcomes.
No event replacement.
No leg-order optimization.
No latency tuning.
No main merge.

Passing V0.9 still would not authorize micro-live; it would justify a separate candidate-level execution authority review.
