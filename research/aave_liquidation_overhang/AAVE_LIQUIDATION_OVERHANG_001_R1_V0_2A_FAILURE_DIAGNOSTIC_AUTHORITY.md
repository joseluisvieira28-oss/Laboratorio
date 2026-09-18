# AAVE-LIQUIDATION-OVERHANG-001 — R1 V0.2A FAILURE DIAGNOSTIC AUTHORITY

Date: 2026-09-18
Status: SOURCE/RECONSTRUCTION DIAGNOSTIC ONLY / OUTCOME-BLIND

Upstream canonical run:
- GitHub Actions run 35375172202
- artifact AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2A
- classification RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE
- 77 validation targets / 77 validation failures
- health factor, overhang, returns and PnL all unopened

Purpose:
Read the already-produced canonical V0.2A receipt and summarize only:
- validation failure classes/messages;
- archive RPC endpoint statistics;
- counts by audit block;
- counts by token/user only as opaque identifiers if needed for provenance;
- whether failures are uniform across endpoints/blocks or target-specific.

Forbidden:
- recomputing health factor;
- liquidation-overhang predictor;
- price/market outcomes;
- returns/PnL;
- 2025/2026;
- any scientific gate change.

This diagnostic may only identify the next technical source action. It cannot turn the failed V0.2A audit into PASS.
