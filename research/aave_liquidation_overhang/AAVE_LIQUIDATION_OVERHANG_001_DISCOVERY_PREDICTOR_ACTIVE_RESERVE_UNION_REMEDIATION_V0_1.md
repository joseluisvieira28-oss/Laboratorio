# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY PREDICTOR ACTIVE-RESERVE UNION REMEDIATION V0.1

Status: **FROZEN AFTER PREDICTOR-AGGREGATION FAILURE / BEFORE 2023 LIQUIDATION OUTCOMES**
Date: **2026-09-19**

## Trigger

Canonical remediated Discovery run `35427783826`, attempt 2, completed all eight reserve shards as
`DISCOVERY_RESERVE_SHARD_PASS`.

The predictor aggregation then failed before any future-liquidation outcome was opened with:

`DISCOVERY_RECONSTRUCTION_FAILURE — reserve decimals union mismatch`.

## Exact observed source state

Across the eight PASS shard receipts:

- canonical master reserve identities in `selected_reserves`: **37 / 37 unique**;
- reserves with point-in-time decimals inside the frozen 2023 Discovery partition: **27 / 27 unique**;
- ten canonical reserves have no Discovery-period decimals because their exact Aave `init_block` is later than the frozen 2023 Discovery event ceiling.

This is the same temporal eligibility distinction already frozen in
`AAVE_LIQUIDATION_OVERHANG_001_DISCOVERY_RESERVE_DECIMALS_ELIGIBILITY_REMEDIATION_V0_1.md`.

## Root cause

The predictor aggregator conflated:

1. the full canonical R1 reserve master (37 identities); and
2. the active-in-2023 reserve set (27 identities with valid Discovery-period decimals/state).

It incorrectly required the full selected-reserve union to equal the decimals-key union.

## Authorized correction

Predictor aggregation must enforce all of the following:

- exact selected-reserve master union = **37 unique reserves**;
- exact active-2023 decimals union = **27 unique reserves**;
- every active-2023 decimals reserve must belong to the canonical 37-reserve master;
- row-file and row-digest checks remain unchanged;
- no future reserve is synthesized into 2023;
- no active 2023 reserve is removed.

The predictor continues to report:
- `reserve_count = 27`;
- `full_r1_reserve_count = 37`.

## Science unchanged

No change to:
- dates;
- snapshot clock;
- reserve/user state rows;
- Aave oracle values;
- health-factor arithmetic;
- eMode handling;
- 10% primary shock;
- overhang definition;
- next-24h outcome;
- Spearman statistic;
- bootstrap;
- eligibility/pass gates;
- 2024 seal;
- 2025/2026 firewall.

No 2023 future liquidation outcome was opened before this freeze.

## Continuation authority

A continuation workflow may reuse only the exact PASS artifacts from run `35427783826` and execute:

1. corrected predictor aggregation;
2. predictor firewall persistence;
3. only if predictor PASS: frozen 2023 liquidation outcome;
4. only if outcome acquisition PASS: canonical 2023 adjudication.

No reserve replay or scientific mutation is required.
