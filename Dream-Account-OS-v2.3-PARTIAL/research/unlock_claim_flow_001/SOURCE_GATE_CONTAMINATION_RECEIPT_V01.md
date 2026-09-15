# UNLOCK-CLAIM-FLOW-001 — SOURCE GATE CONTAMINATION RECEIPT V0.1

Date: 2026-09-15
Lab: `UNLOCK-CLAIM-FLOW-001`
MVE: `UCF-VESTING-OUTFLOW-24H-001`
Affected research branch: `unlock-claim-flow-001-source-gate-v01`

## Classification

`SOURCE_GATE_EXTERNAL_DISCOVERY_CONTAMINATED — QUARANTINED`

This is a protocol-compliance receipt, not an economic outcome.

## What happened

During outcome-blind wallet-provenance reconnaissance, external block-explorer/search pages were opened to discover possible vesting/distribution contract addresses. Some returned pages mixed the desired contract/source information with current market-price fields and/or current 2026 transaction activity.

The frozen source protocol forbids opening market prices and 2025/2026 data during Source/Data Gate. Therefore the externally retrieved mixed pages are not admissible scientific evidence for this MVE.

## What was NOT done

- No 2023/2024 forward token return was calculated or inspected for this MVE.
- No BTC outcome was calculated or inspected for this MVE.
- No PnL, profit factor or win rate was calculated.
- No signal threshold was calibrated from outcomes.
- No signal window, outcome horizon, promotion gate or expected direction was changed.
- No live trading or exchange mutation occurred.

## Scientific consequence

The pre-registered protocol remains frozen because it predates the exposure. The deterministic EVM candidate scans and allocation-priority receipts already persisted in GitHub are source-only and remain clean; they were generated from the inherited PIT schedule corpus and contain no market outcomes.

The mixed external reconnaissance itself is quarantined and must not be used to qualify a wallet, token, event, threshold, horizon or outcome.

A clean Source Gate remediation must proceed on a new branch using only:
- immutable/historical source material whose requested slice does not expose market outcomes;
- official Git history/contract source;
- direct blockchain contract code/state/logs constrained to the required source windows;
- deterministic source-only receipts.

Current/cross-sectional explorer labels or pages that mix market price/activity are forbidden as final evidence.

## Clean starting point

Clean source-only branch state before this receipt:
`44f5ba29a358f7ca8ea3eff4341962c363fe2dda`

The successor branch must preserve the exact MVE definition and gates from `PRE_SOURCE_PROTOCOL_V01.md` and may not use information from the quarantined external pages.
