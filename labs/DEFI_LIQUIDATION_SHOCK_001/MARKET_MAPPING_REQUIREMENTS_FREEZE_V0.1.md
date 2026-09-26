# DEFI-LIQUIDATION-SHOCK-001 — MARKET MAPPING REQUIREMENTS FREEZE V0.1

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

After SOURCE_SAMPLE_GATE_PASS, derive the exact set of market targets for which metadata-only market-data
feasibility must be established.

This step does not select a venue because of price response and does not open any candle payload.

## Input

- SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json == SOURCE_SAMPLE_GATE_PASS
- SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson
- frozen target semantics from OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.md

## Target mapping from source cluster identity

### Lending
For marginfi, Save0c, Save11 and Kamino:
cluster primary identity is already:
`mint:<collateral_underlying_mint>`

Market-data target identity remains that exact mint.

### Drift liquidate_perp
Cluster identity:
`perp:<perp_market_index>`

Target:
`drift_perp:<perp_market_index>`

### Drift liquidate_spot
Cluster identity:
`spotpair:<asset_spot_market_index>:<liability_spot_market_index>`

Primary outcome target uses only the asset leg:
`drift_spot:<asset_spot_market_index>`

Liability leg remains secondary source metadata and cannot replace the primary target after outcomes.

### Drift liquidate_borrow_for_perp_pnl
Cluster identity:
`perpspot:<perp_market_index>:<spot_market_index>`

Target:
`drift_perp:<perp_market_index>`

### Drift liquidate_perp_pnl_for_deposit
Cluster identity:
`perpspot:<perp_market_index>:<spot_market_index>`

Target:
`drift_perp:<perp_market_index>`

## Output

For every unique source target:
- target identity;
- protocol/class contributors;
- first cluster T0;
- last cluster T0;
- Discovery cluster count;
- OOS cluster count;
- whether any inferential stratum depends on it.

No exchange symbol, quote pair or venue is assigned by this step.

PASS:
`MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS`

Malformed or unsupported source identity:
`MARKET_MAPPING_REQUIREMENTS_BLOCKED_FAIL_CLOSED`

## Firewall

exchange_selected=false
archive_payload_downloaded=false
candles_opened=false
prices_opened=false
returns_computed=false
pnl_computed=false
economic_outcomes_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
merge_main=false
