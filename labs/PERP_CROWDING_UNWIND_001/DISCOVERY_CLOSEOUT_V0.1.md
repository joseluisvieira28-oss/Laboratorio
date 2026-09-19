# PERP-CROWDING-UNWIND-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-19
MVE: `PCU-BTC-24H-TRAILING-CROWDING-001`
Canonical adjudicative run: `35472138378`
Canonical head: `68287ea6332b4ec70f197429c29b89b91352236b`

## Source coverage

**PCU_COVERAGE_FULL**
- 48 / 48 FULL common months
- 2021: 12 / 12
- 2022: 12 / 12
- 2023: 12 / 12
- 2024: 12 / 12

The two earlier Discovery attempts were technical/non-adjudicative and did not produce a completed economic receipt:
- run 35471936589: datetime internal-resolution mismatch before signal construction;
- run 35472028217: mixed ISO summary parse failure after trade construction but before completed receipt.

Both were fixed by narrow representation-only amendments. Economic rules were unchanged.

## Verdict

**DISCOVERY_FAIL_NO_PROMOTION**

Results:
- N = 177
- long N = 57
- short N = 120
- mean net10 = +0.4776%
- median net10 = +0.1811%
- hit rate = 53.11%
- PF net10 = 1.4477
- bootstrap 95% CI mean net10 = [-0.0771%, +1.0516%]
- mean net20 = +0.3776%
- PF net20 = 1.3389
- max losing streak = 6

Year means net10:
- 2021: +0.9536%
- 2022: +0.7592%
- 2023: +0.5006%
- 2024: -0.2813%

Passed frozen gates:
- N >= 60
- mean net10 > 0
- PF net10 >= 1.10
- >=3 positive years
- mean net20 > 0
- PF net20 > 1

Failed frozen gate:
- bootstrap 95% lower bound > 0

## Interpretation

The exact BTC MVE shows economically positive point estimates and survives the frozen 20 bps stress, but the bootstrap confidence interval still includes zero and 2024 is negative. Under the prospectively frozen gate this is **not promotable**.

This is materially more interesting than a broad negative result, but it must not be relabeled SURVIVES or promoted after seeing the outcome.

A new cross-asset test using the **identical frozen mechanism and thresholds** may be opened as an independent candidate/replication. Such a test cannot rescue or rewrite this BTC verdict.

No 2025/2026 data, live trading, wallet access, exchange mutation or merge to main was opened.
