# BTC-CONVEX V0.2 — causal integrity blocker — 2026-09-29

New material event: SOLUSDT active stop is non-monotonic across consecutive append-only forward snapshots.

Prior: run 36096105884 attempt 31; job 109195735854; snapshot 2026-09-29T00:17:00.823774Z; artifact 11005424164; digest 4f9016c18334fa1e500526fdc4d7b805b1fe9c99b1f026a5538ccd748cfe0fba. SOL peak 124.99; active_stop 109.9912; closed trades 0.

Fresh: run 36096105884 attempt 32; job 109209508620; snapshot 2026-09-29T01:11:01.478860Z; artifact 11006788879; digest 7a801fdc01171b04ebb7ec285d73c9b44ef6b3b2a8d04ed8e6d4cd455638a6d8. SOL peak 124.99; active_stop 108.57851136; closed trades 0.

The position remained open and peak stayed 124.99, but active_stop fell back to the initial hard stop. The frozen implementation conditions trailing activation on current-close return each bar, so a later close below ACT can reset an already-raised stop. The current validator checks only active_stop >= initial_stop within one snapshot and therefore does not catch cross-snapshot monotonicity.

Governance: CAUSAL_INTEGRITY_BLOCKED. Do not credit subsequent outcomes toward A/B/C until state-transition semantics are reconciled. Frozen rule, universe, costs, timeframe and direction remain unchanged.

Detection state: 4/4 sources PASS; no source gaps; signals BTC/ETH/SOL=1 each, BNB=0; open BTC/ETH/SOL; no pending entries; 0 closed trades; A/B/C false.
