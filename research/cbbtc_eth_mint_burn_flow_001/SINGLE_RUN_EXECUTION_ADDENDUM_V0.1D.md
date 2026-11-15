# CBBTC-ETH-MINT-BURN-FLOW-001 — SINGLE-RUN EXECUTION ADDENDUM V0.1D

Frozen: 2026-09-27
Scope: orchestration only.

## Purpose

GitHub Actions runner availability is currently constrained and the source gate plus downstream continuation are separate workflows.

This addendum authorizes a single fail-closed run to execute the already-frozen chain in sequence using one runner:

1. exact SOURCE_GATE_V0.1;
2. only if SOURCE_PASS, exact outcome-blind flow census;
3. only if census PASS, pre-frozen q10/q90 calibration;
4. only if calibration PASS, H2-2025 outcome-blind predictor sample gate;
5. only if sample PASS, frozen 2025 BTC mechanism Discovery.

No scientific parameter, source, period, threshold, direction, horizon, sample minimum, bootstrap rule, or protected-data boundary changes.

## Hard boundaries

- 2026 remains CLOSED.
- OOS remains CLOSED.
- PnL remains CLOSED.
- no trading, orders, exchange mutation or wallet mutation.
- no main merge.
- source/census/sample terminal failures close the exact lab per GOVERNANCE_DECISION_TREE_V0.1.
- FLOW_DISCOVERY_PASS still requires a separate future OOS authority.

## Concurrency

The single-run workflow uses the same source-gate concurrency group with cancel-in-progress=true so it supersedes an obsolete queued standalone source-gate attempt rather than duplicating scientific execution.
