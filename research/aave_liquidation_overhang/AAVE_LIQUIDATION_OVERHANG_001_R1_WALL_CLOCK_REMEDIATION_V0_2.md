# AAVE-LIQUIDATION-OVERHANG-001 — R1 WALL-CLOCK REMEDIATION V0.2

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE 240-MINUTE AUDIT EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## New operational finding

The V0.1 remediation increased the exact deterministic audit timeout from 45 to 120 minutes.
Canonical run `35355395431` reached the unchanged audit execution step and was cancelled at the 120-minute ceiling with no audit receipt and no scientific/reconstruction verdict.

Classification: **OPERATIONAL_WALL_CLOCK_CANCELLATION / NO SCIENTIFIC VERDICT**.

## Sole permitted remediation

Increase only the workflow timeout:
- from: `120` minutes
- to: `240` minutes

The audit implementation and all scientific/source semantics remain unchanged.

Forbidden changes:
- no sharding;
- no sample-user filtering or replacement;
- no reserve filtering;
- no target dropping;
- no RPC quorum relaxation;
- no arithmetic changes;
- no event-semantic changes;
- no source identity changes;
- no pass/fail threshold changes;
- no 2025/2026 access;
- no health factor / overhang / future liquidation outcome;
- no market prices / returns / PnL;
- no live trading / orders / wallets / exchange mutation;
- no merge to main.

The first workflow run triggered by the exact timeout-only workflow commit is the only admissible V0.2 audit attempt. A failure or cancellation remains fail-closed.
