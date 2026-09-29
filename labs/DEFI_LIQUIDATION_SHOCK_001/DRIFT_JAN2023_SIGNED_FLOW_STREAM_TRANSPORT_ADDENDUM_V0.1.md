# DLS — DRIFT JAN-2023 SIGNED-FLOW STREAM TRANSPORT ADDENDUM V0.1

Date: 2026-09-29
Status: FROZEN TECHNICAL TRANSPORT ADDENDUM
Parent freeze: DRIFT_JAN2023_REALIZED_SIGNED_FLOW_POPULATION_FREEZE_V0.1.md

This addendum changes transport only.

Scientific population, event decoder, exact identity binding, realized/non-realized rules,
direction mapping, conservative coverage formula, thresholds, and firewall remain identical.

## Alternate transport

Instead of one SQD request per target slot, an implementation may query the same public/free
Solana finalized stream over the frozen January interval using:
- Drift program ID filter on logs;
- parent transaction inclusion;
- block number for deterministic stream advancement.

The implementation must:
- keep only exact canonical signatures from the frozen 3,179-candidate population;
- preserve each log's transactionIndex and instructionAddress;
- bind candidates independently exactly as in the parent freeze;
- never use the absence of a target from an incomplete/failed stream as proof of non-realization;
- mark unrecovered canonical signatures SOURCE_EVIDENCE_INCOMPLETE;
- fail closed on non-advancing streams, schema conflicts, or hard transport errors.

Stream pagination/chunk boundaries are technical and cannot change adjudication.

A result is authoritative only if every stream request advances deterministically to documented
termination or the remaining unrecovered candidates are conservatively counted as incomplete.

No market outcomes are accessed.

Firewall unchanged:
prices=false
returns=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
