# STETH-REDEMPTION-BASIS-002 — TIMESTAMP MAPPING TRANSPORT CLARIFICATION V0.1A

Date: 2026-09-18
Status: FROZEN BEFORE FIRST SOURCE EXECUTION

This clarification changes no source snapshot, economic rule or protected period.

The V0.1 authority requires deterministic mapping of the final target:
2024-12-31T12:00:00Z

A first-block-at/after timestamp binary search necessarily requires block-header bracketing on both sides of the target.

Therefore, for TIMESTAMP MAPPING ONLY:
- block headers may be read up to the already-proven 2024-12-31 terminal block 21,525,890;
- header reads contain no contract state, log payload, market price, return or economic predictor;
- any header timestamp beyond 2024-12-31T23:59:59Z is forbidden.

Once the exact final 12:00 mapping block is found:
- all contract bytecode/state calls for the final edge use only that exact mapped block;
- all event-log windows are capped at or before that exact mapped block;
- no source-state or source-log traversal after the mapped final 12:00 block is authorized.

The first target remains:
2023-05-16T12:00:00Z

The final target remains:
2024-12-31T12:00:00Z

Expected daily snapshot population remains:
596

No market outcomes are authorized.
