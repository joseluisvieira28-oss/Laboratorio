# CED-1D-V1 — V3 BOUNDARY RE-ADJUDICATION IMPLEMENTATION FREEZE — 2026-09-18

**Status:** FROZEN BEFORE REAL BOUNDARY-ADJUSTED TARGET METRICS  
**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`

## Frozen implementation

Implementation:
`Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/ced_1d_v3_boundary_readjudication_v01.py`

Implementation commit:
`127682c9aac379802fd9d2d1c41577f738bde84f`

Tests:
`Dream-Account-OS-v2.3-PARTIAL/tests/test_ced_1d_v3_boundary_readjudication_v01.py`

Test commit:
`1cf4accb0188ac3e6129a54eb72becba040127db`

## Frozen dependencies and identity gates

- historical mapped closeout ZIP SHA256:
  `d590b2fe3b86baa9b9b0c1e092cf53c6cb0067ebcafb9fd7a21002dd2df50841`
- frozen `src/closeout.py` SHA256:
  `71525ab74c926c72c94e952e2d193255901be296f1d0cd32f9bfa90118ba01f8`
- historical closeout output SHA256 independently recovered:
  `8b30a95606a0949a912fa8d1475e63c9431263c7568bf0b2d3df4f8373c47416`
- reproduced RAW Discovery 7/7 logical input members match the original closeout runner's exact `input_pins.json`.
- derived daily SHA256:
  `b92741d682a704a237cc1ab1a4d1fb0beb13798b11993ddde9ef54bcd4f3ab20`
- contract SHA256:
  `4a6ee27a8b6fd66dcc89e3d2b4211d3f5d5c8020c151f8908f081108803acfb4`
- dataset fingerprint:
  `0b3de834cf5a126cb348596a466ce191e956640f4e7c3d8d3fbc8f38e1c5ad93`

Historical mapped closeout regression suite was executed unchanged: **69/69 PASS**.
The V3 boundary wrapper synthetic/integration suite was executed before real adjusted target metrics: **9/9 PASS** plus Python compile PASS.

## Frozen target scope

Exactly three historical survivors may be re-adjudicated:

1. `CED1D-0031` — AVAXUSDT — Momentum 20D — CONTINUATION — Hold 1D
2. `CED1D-0241` — SOLUSDT — Momentum 20D — CONTINUATION — Hold 1D
3. `CED1D-0251` — SOLUSDT — Momentum 60D — CONTINUATION — Hold 1D

Non-target cells are not routed and cannot become new survivors. Only the exact frozen parameter-neighbour dependencies required by the V0.2 stability rubric may have dependency metrics calculated:
`CED1D-0033, CED1D-0041, CED1D-0243, CED1D-0253, CED1D-0261`, plus the three targets themselves.

## Boundary rule

Authority:
- `CED-4H-V1 — PRE-DISCOVERY AMENDMENT 01 — V0.1`
- Drive ID `1i06x1R1iFerQYEtKSoJvhD9ONtR6y_qx-j1k8Uj_79w`
- CED-1D addendum commit `96d783275e8474dc4a30a14eed16f5f23c29e9b9`

Rule:
- UTC week Monday 00:00 to next Monday 00:00.
- eligibility anchor = **signal completion day**.
- first complete week = 2021-01-04.
- complete-week end is 2024-12-30 exclusive.
- boundary rows remain in immutable ledger/audit.
- boundary rows are excluded from sample gates, cost aggregation, temporal/stability/concentration, bootstrap, Scout Score and routing.
- bootstrap arithmetic remains frozen V0.2; only week attribution is mapped to signal completion.

## V3 metrics frozen before outcome

For each target, the wrapper must report:
- BASE nonfunding mean at frozen 10 bps;
- STRESS 14 and SEVERE 20 sensitivities;
- finite profit factor at BASE = sum positive BASE-net / absolute sum negative BASE-net;
- BASE win rate and median;
- 5th/95th percentiles using frozen linear percentile interpolation;
- cumulative event-sequence max drawdown in BASE-net bps;
- V0.2 sample, concentration, temporal, neighbour and Scout Score diagnostics;
- V0.2 centered-null weekly bootstrap with 9,999 resamples and seed 20260908, using signal-completion week attribution;
- funded claim status remains `NOT_TESTABLE`.

BH q is deliberately **not recomputed** because V3 scope is locked to the three survivors and their neighbour dependencies; V0.2 BH is diagnostic-only and not a Scout survival requirement. No 300-cell family-wide re-routing is authorized.

## Firewall

Before this implementation freeze:
- no boundary-adjusted target result was executed;
- no 2025 outcome was opened;
- no 2026+ data was opened;
- no parameter, direction, lookback, horizon, cost band, seed or threshold was changed;
- no new survivor was created;
- no Promotion V3 verdict was assigned.

Next authorized action: execute this frozen wrapper once against the exact reproduced RAW Discovery and adjudicate only the three frozen targets.