# CMM-DRV-001 — TECHNICAL INPUT BINDING V0.1

Status: FROZEN BEFORE 2025 CMM-DRV-001 OUTCOMES

Parent warmup state ledger:
- path: cmm001/discovery_results/CMM001_DAILY_STATE_LEDGER_V01.csv
- Git blob SHA: c30a38638dcbd8dd33a5a627ad15a3a7096011ca

The runner may read only the parent daily state fields required to continue the frozen rolling state machine:
date, S_raw, O_raw, R_raw, L_raw, G.

It MUST NOT read the parent event ledger or any parent return/PnL field.

This binding is technical/provenance only and does not change the CMM-DRV-001 scientific rule.
