# LCOD AAVE SOURCE RECON RECEIPT V0.1

Date: 2026-09-24
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Verdict: SOURCE_CAPABILITY_PASS__COMPONENT_PAYLOAD_PROBE_PENDING

## Evidence reused from the active AAVE-HF-CROWDING branch

Read-only receipts captured from the official Aave MCP on 2026-09-24 report:
- classification OFFICIAL_AAVE_MCP_CREDIT_SOURCE_CAPABILITY_PASS;
- 53 tools visible;
- get_user_positions present;
- get_user_summary present;
- get_user_summary_history present;
- get_position_items present;
- get_reserve_details present;
- no action tool called;
- no mutation;
- no market returns or PnL opened.

The live schema description recorded in that branch states:
- get_position_items exposes individual V4 supplies/borrows including principal and accrued interest;
- get_reserve_details exposes V4 risk parameters;
- in V4, collateralFactorPct is described as the liquidation boundary because V4 has no separate liquidationThreshold field.

## Existing collector limitation

The AAVE-HF-CROWDING population/calibration code deliberately does NOT retain:
- debt values;
- collateral values;
- price values;
- wallet addresses in output;
- individual health-factor values.

Therefore it cannot serve as the canonical LCOD component snapshot.

## New LCOD probe

Committed:
- research/liquidation_convexity_oracle_distance_001/lcod_source_probe_v01.py
- .github/workflows/lcod-001-source-component-probe-v01.yml

Purpose:
- read tools/list live;
- sample borrowers through the existing reserve-holder route;
- inspect get_user_positions/get_position_items/get_user_summary/get_reserve_details field paths;
- retain hashed borrower identities only in the evidence receipt;
- never open market returns/PnL.

## Execution status

The current ChatGPT runtime could not resolve mcp.aave.com over its local network.
A branch push workflow was prepared, but a workflow run was not independently observable through the available GitHub connector in this session.

Therefore:
- source capability = PASS;
- component payload sufficiency = NOT YET PROVEN;
- HF reconstruction = NOT YET PROVEN;
- LCOD remains SOURCE_PARTIAL.

No outcome gate is open.
