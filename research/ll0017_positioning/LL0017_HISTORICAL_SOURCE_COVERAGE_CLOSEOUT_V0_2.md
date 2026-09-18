# LL-0017 — HISTORICAL SOURCE COVERAGE CLOSEOUT V0.2

Date: 2026-09-18
Branch: `ll-0017-positioning-ratio-v0.1`

## Verdict

**SOURCE_TEMPORAL_COVERAGE_INADEQUATE**

This is a source/data verdict only. It is **NOT NO_EDGE**, not negative expectancy, and not an economic outcome.

## Canonical run

- GitHub Actions run: `35366119745`
- Canonical aggregate artifact ID: `10556079444`
- Frozen date envelope: 2021-01-01 through 2024-12-31
- Expected calendar days: 1,461
- Ratio numeric values parsed: false
- Prices opened: false
- Returns opened: false
- PnL opened: false
- 2025 accessed: false
- 2026 accessed: false

## Result

- resolved source-valid days: **1,450 / 1,461**
- failed days: **11**
- days with exactly 288 normalized 5-minute timestamps: **1,395**
- frozen minimum full-day requirement: **1,454** (99.5% of 1,461, rounded up)
- minimum normalized timestamps on otherwise admitted days: **280**
- total normalized timestamps: **417,477**
- exact provider duplicate rows collapsed under pre-frozen V0.1A rule: **38,578**

Three shards returned source-temporal failures; the other five passed. The aggregate therefore correctly classified the exact census as `SOURCE_TEMPORAL_COVERAGE_INADEQUATE`.

## Scientific decision

STOP this exact historical source MVE.

Do not:
- lower the 99.5% full-day gate after seeing this result;
- redefine a full day below 288 snapshots;
- discard the 11 failed days;
- select favorable subperiods;
- infer missing positioning values;
- open ratio values, prices or outcomes under this exact MVE;
- relabel this as NO_EDGE.

A second identical census may exist operationally after this closeout, but it cannot replace or rescue the canonical first full census because the failure is source coverage under the prospectively frozen gate, not a demonstrated transport-only defect.

## What survives

The source-schema finding remains valid:
- Binance Data Vision exposes the required distinct fields:
  - `count_toptrader_long_short_ratio`
  - `sum_toptrader_long_short_ratio`
  - `count_long_short_ratio`
- the exact 2021-2024 full-coverage MVE failed only the frozen historical coverage standard.

A materially different future source architecture may be considered only under a new prospective authority before any ratio values or market outcomes are opened.
