# V0.1A — Acquisition correction before economic outcomes
2026-10-06; source-only. No change to mechanism, window, sample requirement or inference.
Initial run 37441092166 (fca42a49) failed to enter the configuration census. Requiring a genesis header incorrectly couples historical V3 access to irrelevant pre-deployment pruning. Remove genesis prerequisite; Ethereum header search starts at 16490000 (same known pre-activation source baseline used by prior lab). Other boundary and state errors are retained.
Separate configuration-log acquisition from archival eth_call capability. A timestamp boundary PASS permits configuration census even when archival state fails. It cannot produce SOURCE_GATE_PASS.
Increase exact bounded sparse SQD request window to 5m blocks with continuation after the last returned header and raw hash receipts; does not alter the scientific envelope. Add the documented AssetCollateralInEModeChanged signature for structural coverage.
Treat execution counts as potential shocks only, never accepted queued governance events. Historical deployments/upgrade lineage/eMode/exposure still require proof.
Do not classify incomplete census as INSUFFICIENT_SAMPLE. A full causal SOURCE gate cannot pass on configuration count alone.
