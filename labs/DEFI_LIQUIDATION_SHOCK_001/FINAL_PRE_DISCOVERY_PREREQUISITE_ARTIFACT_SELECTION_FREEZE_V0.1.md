# DEFI-LIQUIDATION-SHOCK-001 — FINAL PRE-DISCOVERY PREREQUISITE ARTIFACT SELECTION FREEZE V0.1

Date: 2026-09-27
Status: FROZEN / OUTCOME-BLIND / FAIL-CLOSED

## Required artifact groups

1. Global Field:
   `dls-global-field-coverage-final-v01`

2. Source Sample Gate:
   `dls-source-cluster-sample-gate-v01`

3. Market Data Source Feasibility:
   `dls-market-data-source-feasibility-v01`

## Selection

For each exact artifact name:
- ignore expired artifacts;
- sort by created_at descending then artifact id descending;
- select the newest;
- never inspect scientific classification to choose an older artifact.

The newest artifact must contain the exact prerequisite receipt and classification:

- GLOBAL_FIELD_COVERAGE_FINAL_RECEIPT_V0.1.json
  -> GLOBAL_FIELD_COVERAGE_FINAL_PASS

- SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json
  -> SOURCE_SAMPLE_GATE_PASS

- MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json
  -> MARKET_DATA_SOURCE_PASS

A newer BLOCKED/PENDING receipt cannot be bypassed by selecting an older PASS.

## Firewall

prices_opened=false
returns_opened=false
pnl_opened=false
economic_outcomes_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
merge_main=false
