# ARQ-002 CSP-003 — NAMESPACE RECONCILIATION — 2026-09-23

## Administrative collision

A parallel project chat independently created and executed:
- LAB_ID: `ARQ-002-CSP-003`
- branch: `arq002-csp003-validity-mask-v0.1`
- Discovery period: 2024
- canonical run: 35910976864
- final classification: DISCOVERY_FAIL_NO_PROMOTION

This branch was created concurrently under the same nominal LAB_ID:
- branch: `arq002-csp003-clean-2022-2023-v0.1`
- Discovery period: 2022
- 2023 replication pre-frozen but never released unless 2022 survived
- corrected canonical Discovery run: 35912921069
- final classification: DISCOVERY_FAIL_NO_PROMOTION

## Administrative alias

To prevent future ambiguity, artifacts on THIS branch should be referred to as:

**ARQ-002-CSP-003-CLEAN-2022**

This is an administrative alias only.

It does NOT:
- change the frozen hypothesis;
- change any threshold, source rule, cost, event rule, direction or horizon;
- change the scientific receipt;
- merge the 2022 and 2024 samples;
- treat either run as a rescue of the other.

## Scientific relationship

The two executions are temporally separate tests of materially the same CVD + sweep/reclaim + OI/funding confirmation mechanism.

The clean-2022 branch was frozen and run without using the parallel 2024 CSP-003 result to tune its science.

Both independently closed DISCOVERY_FAIL_NO_PROMOTION.

2023 remains unopened on this branch because its pre-frozen release condition required all 2022 Discovery gates to pass.

## Canonical references for clean-2022 branch

- Source closeout commit: c669e53fbfb265e9c7cb2366fdb8e2b3fddfbe26
- Technical correction A: f9e1ecb6883649aae5016f05bd7de66e09341253
- Corrected Discovery run: 35912921069
- Final Discovery receipt SHA256: 5c749314e6ca0774f9715f5b808cd02919de3a0f383962bd8b6fd848ed4ed950
- Discovery closeout commit: 6d3ff931448edccb46b8c592d12a9a8674b4d81e
