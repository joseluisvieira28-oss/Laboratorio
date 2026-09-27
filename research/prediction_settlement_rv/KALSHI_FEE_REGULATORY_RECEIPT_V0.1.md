# PREDICTION-SETTLEMENT-RV-001 — KALSHI FEE REGULATORY RECEIPT V0.1

Date: 2026-09-27
Status: SOURCE_PROVENANCE / RESEARCH_ONLY
Lab: PREDICTION-SETTLEMENT-RV-001

## Purpose

Freeze the fee provenance route for Kalshi before any package economics are opened.

## Primary authority

Kalshi regulatory fee-schedule landing:
https://kalshi.com/regulatory/fee-schedule

Official fee-schedule PDF inspected on 2026-09-27.

General event-contract trading fee formula in the official schedule:
- taker fee = round up(M × 0.07 × C × P × (1-P))
- maker fee = round up(M × 0.0175 × C × P × (1-P))
- P = contract price in dollars
- C = number of contracts
- M = fee multiplier defined by the applicable schedule
- no settlement fee under the general schedule.

The KXBTCD series was not identified in the inspected non-standard-series list. Therefore the later economic protocol may use the general formula only if a fresh schedule snapshot immediately preceding that protocol still shows no KXBTCD-specific override.

## API cross-check

Source-readiness run:
36339649202

Artifact:
10938113181

The exact probed KXBTCD market metadata contained no fee-named fields. Therefore market JSON is not accepted as fee authority.

## Fail-closed rule

Before any economic calculation:
1. retrieve the then-current official Kalshi fee schedule;
2. preserve the exact bytes/PDF hash or equivalent immutable receipt;
3. search explicitly for KXBTCD and the exact matched series;
4. if a series-specific fee exists, it overrides the general formula;
5. if provenance is ambiguous, SOURCE_DATA_PASS remains false.

No PnL or package economics are authorized by this receipt.
