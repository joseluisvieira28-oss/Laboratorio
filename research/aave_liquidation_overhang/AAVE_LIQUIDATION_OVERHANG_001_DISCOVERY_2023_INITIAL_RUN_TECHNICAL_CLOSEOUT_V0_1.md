# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY 2023 INITIAL RUN TECHNICAL CLOSEOUT V0.1

Date: 2026-09-18
Status: **SUPERSEDED TECHNICAL DIAGNOSTIC / NOT SCIENTIFIC ADJUDICATION**

## Initial Discovery run

Run: `35393804723`
Head: `c5a317e56e6a090313add1c6eca192d3d934b963`

The run passed:
- exact R1 `RECONSTRUCTION_DATA_PASS` preflight;
- canonical 2023 calendar;
- global/eMode/oracle Discovery source reconstruction.

Multiple reserve shards then emitted `DISCOVERY_RECONSTRUCTION_FAILURE` before health factor, overhang predictor or future liquidation outcomes were opened.

## Exact technical defect

The reserve-shard implementation required aToken `Initialized` decimals for every canonical master reserve assigned to a shard.

Several canonical reserves were initialized only **after** the frozen 2023 Discovery event ceiling, while the same code already excluded such reserves from 2023 daily state targets through `init_block > snapshot_block`.

Thus the preliminary decimals check incorrectly required Discovery-period token metadata for reserves that did not yet exist in the Discovery partition.

Canonical 2023 event ceiling:
`18,908,894`.

Every reserve identified in the observed missing-decimals failures had:
`init_block > 18,908,894`.

This is a temporal master-data eligibility defect, not a market result.

## Safety

Observed failed shard receipts show:
- no health factor computed;
- no liquidation-overhang predictor computed;
- no future LiquidationCall outcome opened;
- no 2024 outcome opened;
- no 2025/2026;
- no market return;
- no PnL;
- no live trading or exchange mutation.

## Canonical remediation

Prospectively frozen:
`AAVE_LIQUIDATION_OVERHANG_001_DISCOVERY_RESERVE_DECIMALS_ELIGIBILITY_REMEDIATION_V0_1.md`

Remediation rule:
a reserve requires Discovery-2023 decimals iff
`init_block <= discovery_event_to_block`.

No active-2023 reserve is dropped.
No future reserve is added early.
No scientific parameter changes.

Canonical remediated run:
- run `35397902787`
- head `7e7f157458d9ecc2c8fb3d67d50a2d3403fc38cb`.

## Governance

Regardless of any later completion state of run `35393804723`:

- do not issue edge/no-edge from it;
- do not aggregate its failed/passing shards into a verdict;
- do not use it for parameter tuning;
- do not unseal 2024 from it.

Only the exact remediated lineage beginning with run `35397902787` may adjudicate Discovery 2023 under the frozen protocol.
