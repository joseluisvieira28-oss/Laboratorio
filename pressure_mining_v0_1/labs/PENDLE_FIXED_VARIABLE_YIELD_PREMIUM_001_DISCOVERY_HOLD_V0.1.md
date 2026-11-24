# PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001 — DISCOVERY HOLD V0.1

Date: 2026-09-27
Status: PRE-OUTCOME HOLD / ECONOMIC PROVENANCE INCOMPLETE

## Decision

The T-30 Discovery contract was frozen before outcomes, but it is **not authorized for execution**.

No implied-APY premium outcome has been computed.

## Why execution is held

The source-completeness gate proves that current Pendle metadata identifies 34 expired Ethereum markets with empty/no current points metadata and usable historical APY schema.

That does **not** prove that those markets were free of economically material off-chain points at the historical T-30 observation.

Official Pendle documentation states:
- YT can receive underlying protocol points;
- points can materially affect YT/PT valuation;
- points have unknown monetary value and Pendle may assume zero in displayed yield/PnL contexts;
- point multipliers can vary by protocol and over time.

Therefore current empty points metadata is not sufficient point-in-time historical evidence for an economic fixed-vs-variable comparison.

## Scientific consequence

The frozen T-30 protocol is preserved as a prospectively written design, but execution remains blocked until one of the following is proven **without opening premium outcomes**:

1. a historical point-in-time source showing that each eligible market had no points at T-30; or
2. a defensible historical point valuation method frozen prospectively; or
3. an objective protocol/population rule with primary-source evidence that off-chain points were economically absent for the full observation window.

A current metadata field alone is insufficient.

## Current state

SOURCE_COMPLETENESS_PASS
+
ECONOMIC_PROVENANCE_INCOMPLETE
=
DISCOVERY_BLOCKED_PRE_OUTCOME

This is not NO_EDGE and does not invalidate the broader Pendle fixed-vs-variable hypothesis.

## Firewall

premium_outcomes_opened=false
2025_plus_opened=false
pnl_computed=false
live_trading=false
orders=false
exchange_mutation=false
capital=false
main_merge=false
post_outcome_tuning=false
