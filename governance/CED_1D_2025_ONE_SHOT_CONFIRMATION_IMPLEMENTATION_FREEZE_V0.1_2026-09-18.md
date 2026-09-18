# CED-1D-V1 — 2025 ONE-SHOT CONFIRMATION IMPLEMENTATION FREEZE — V0.1 — 2026-09-18

**Status:** IMPLEMENTATION FROZEN BEFORE 2025 STRATEGY OUTCOMES  
**Branch:** ced-1d-v3-byte-recovery-2026-09-17

## Scientific authority

Controlling Confirmation authority:
- governance/CED_1D_V3_2025_CONFIRMATION_EXECUTION_FREEZE_2026-09-18.md
- parent authority commit: ad0c4813c57cc3a18436e6c5505c3c7ac12c19d0
- controlling V3 Discovery re-adjudication closeout: 2927172d237d7aa188e7f191eda005d18c694545

Funding mark-price uncertainty authority:
- governance/CED_1D_2025_FUNDING_MARK_PRICE_INTERVAL_BOUND_AMENDMENT_V0.2_2026-09-18.md
- commit: 206a91060e00b6f5a5bb4daf4f86a120478372b6
- source mapping correction: CED_1D_2025_FUNDING_MARKPRICE_INTERVAL_SOURCE_AMENDMENT_V0.4
- commit: fbac8d695bbea3a77e35d0b6980e3c0682c1669d

## Frozen implementation identities

One-shot runner:
- path: Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/ced_1d_2025_confirmation_runner_v01.py
- implementation commit: 609ecde6dd237cc78f3a495220e7efe16d463be3
- Git blob SHA: 453656bcc0e345a3aaeb42305386d388a660cd3c

Synthetic QA:
- test path: Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/tests/test_ced_1d_2025_confirmation_runner_v01.py
- test commit: 78246606e681665b246c630759ca544b0a2481e4
- Git blob SHA: c8ffd08a824326aeb6fa491dc9ed71f79079c0d7
- QA workflow run: 35340731810
- conclusion: SUCCESS
- real 2025 strategy outcomes opened by QA: false

Original scientific implementation dependency:
- CED-1D-V1-RUNNER-FREEZE-V0.3.zip
- SHA256: df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958
- hypotheses.py SHA256: dc52cdc16aee0ba586ec7081a39ce68d62c5544e9bd27186255b4d9a87368693
- the one-shot runner imports the original V0.3 Momentum signal, valid-lookback and execution functions by exact hash.

## Price source gate

Frozen source manifest:
- CED_1D_2025_SOURCE_MANIFEST_V0.2
- Git blob SHA: 5984e48acf4846068f471645d4d9c8242cfa8137
- 32 files: AVAXUSDT/SOLUSDT 2024-09 through 2025-12
- 2024-09..12 = warm-up only
- 2025 = independent Confirmation source

Source gate implementation:
- ced_1d_2025_source_gate_v03.py
- Git blob SHA: 61c12cd20c1db94bdf2fbdf4056f5004269c2368

Executed source evidence:
- GitHub Actions run: 35339925864
- artifact ID: 10544541993
- artifact digest: sha256:34b0bd7ef27c2ea4532124dfa6ae90b3adaa72e5321d74ea2840ac624bd76f95
- receipt fingerprint: f6b488fbc2562df29916a30e651f48a4af48b19106ff623dc977d32fbf66cac7
- result: SOURCE_DATA_PASS
- files: 32 / 32 PASS
- failures: 0
- 2025 strategy outcomes computed: false
- 2026 accessed: false

## Funding-rate source gate

Executed evidence:
- GitHub Actions run: 35339781808
- artifact ID: 10544646577
- artifact digest: sha256:95f20a1a01589dfde441d0499b752f472d2e3d7611c88f2d5ba76abe26a47227
- receipt fingerprint: 85cb288d811e65d1bfb2d4b104b1f7b807a9b35c6ec89b21dfaa5e111c78fc90
- result: FUNDING_SOURCE_PASS
- AVAXUSDT: 1095 canonical 2025 funding records
- SOLUSDT: 1095 canonical 2025 funding records
- 2025 strategy outcomes computed: false
- 2026 accessed: false

## Funding mark-price interval source gate

Implementation:
- ced_1d_2025_funding_markprice_interval_gate_v04.py
- Git blob SHA: 6b12ef2e7f9c10cf47b6afd5d677110fd4f05ca0
- source amendment Git blob SHA: 1f07af99871ae5bd21e71c08f3316c65632d19c2

Executed evidence:
- GitHub Actions run: 35340535553
- artifact ID: 10545350756
- artifact digest: sha256:47478799d70a1c2b30265b48ab0950e3b1d56a0b3c457011314845189e71e8dc
- receipt fingerprint: c7552387cad825063f7e238cd2c4939fabd08891710be2f70e1b74b8fa5504d0
- result: FUNDING_MARKPRICE_INTERVAL_SOURCE_PASS
- AVAXUSDT settlements bound: 1095 / 1095
- SOLUSDT settlements bound: 1095 / 1095
- missing settlements: 0
- nearest-neighbour: forbidden
- point estimate selected: none
- preserved source-supported mark interval: LOW/HIGH
- 2025 strategy outcomes computed: false
- 2026 accessed: false

## Frozen one-shot behavior

The runner:
- evaluates exactly the fixed 8-cell Holm family;
- allows Confirmation verdicts only on the 3 frozen targets;
- uses exact original V0.3 Momentum and execution semantics;
- uses complete signal-week inference only;
- applies BASE14 and STRESS20;
- applies source-supported funding LOW/HIGH bounds;
- uses identical 9999 complete-week bootstrap draws with seed 20260908;
- uses Holm FWER 0.05 across all 8 cells;
- applies V0.2 sample, temporal, neighbour, concentration and leave-one-month-out gates;
- emits both conservative LOWER and optimistic UPPER funded paths;
- declares a robust PASS only if the LOWER path passes every strict gate;
- declares a robust FAIL only if the UPPER path still fails the strict gate;
- otherwise declares funding interval ambiguity.

## One-shot boundary

At the time of this implementation freeze:
- 2025 strategy outcomes opened: false
- 2026 accessed: false
- live trading: false
- exchange mutation: false
- orders: false
- wallets: false
- alerts/webhooks: false
- main merge: false

The next permitted action is creation of exactly one explicit 2025 access authorization record, followed by one deterministic execution of this frozen implementation.
