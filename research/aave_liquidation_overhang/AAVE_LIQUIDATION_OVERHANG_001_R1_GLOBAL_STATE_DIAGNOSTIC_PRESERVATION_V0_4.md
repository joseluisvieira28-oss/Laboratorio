# AAVE-LIQUIDATION-OVERHANG-001 — R1 GLOBAL STATE DIAGNOSTIC PRESERVATION V0.4

Date: 2026-09-18
Status: FROZEN BEFORE RERUN
Scope: reconstruction-only / outcome-blind

## Trigger

V0.3 global-state/oracle run inside workflow 35378904880 returned RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE.

The V0.3 wrapper then replaced the base receipt failure with:
V0.3 provider-set binding mismatch

because archive_rpc_stats was absent. This destroyed the original technical cause and prevents legitimate adjudication.

## Exact remediation

Rerun the exact frozen global-state/oracle logic with the same:
- block envelope 16,490,000..21,525,890;
- canonical R1_AUDIT_PASS;
- R0 bootstrap;
- eMode/provider/oracle event logic;
- three archive providers;
- quorum=2;
- exact oracle validation semantics.

The wrapper may validate provider-set binding only if archive_rpc_stats exists.
If the base runner fails before archive RPC validation, preserve its original classification and failure verbatim.

No scientific rule changes.
No event changes.
No provider changes.
No horizon changes.
No health factor.
No overhang.
No outcomes.
No 2025/2026.
No trading/exchange mutation/main merge.
