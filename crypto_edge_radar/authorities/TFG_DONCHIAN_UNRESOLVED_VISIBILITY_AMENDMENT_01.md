# TFG-DONCHIAN-REGIME-ADAPTATION-V1 — UNRESOLVED VISIBILITY AMENDMENT 01

**Status:** OPERATIONAL DIAGNOSTIC ONLY / FROZEN BEFORE CODE CHANGE

The forward contract is unchanged. An unresolved signal is not a resolved trade and may never be counted as one.

The frozen maximum hold is 80 x 12H bars. The current metrics surface reports only a count of signal keys without a resolution, which can conflate:
- a legitimate forward path still maturing inside the frozen maximum-hold window;
- a path that is already past the frozen time-exit boundary and therefore requires reconciliation review;
- a malformed legacy evidence payload whose exact entry binding cannot be classified.

This amendment authorizes diagnostic classification only:
- MATURING_WITHIN_FROZEN_MAX_HOLD
- OVERDUE_RECONCILIATION_REVIEW
- UNCLASSIFIED_MISSING_ENTRY_BINDING

No synthetic resolution, no reconstruction, no changed stop/target/time-exit, no changed cost, no signal deletion, no readiness credit and no live authority are introduced. The existing readiness gate continues to require unresolved_execution_paths == 0.
