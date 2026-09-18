# CED-1D-V1 — V3 BOUNDARY-WEEK RE-ADJUDICATION ADDENDUM — 2026-09-18

**Status:** FROZEN BEFORE V3 SURVIVOR RE-ADJUDICATION METRICS  
**Lab:** CED-1D-V1  
**Scope:** historical Discovery 2021–2024; exactly three already-frozen Momentum survivors  
**Purpose:** resolve the historical `INFERENCE_BLOCKED_INCOMPLETE_BOUNDARY_WEEK` operational blocker without changing hypothesis, parameters, costs, sample floors, statistical thresholds, candidate identity, or protected-data policy.

## 1. Opening evidence

The exact frozen Discovery reproduction completed successfully in GitHub Actions run **35336456618**, head SHA `227c1c328e1fbf1127d986cc074f4653b6d29762`.

Required identity/firewall assertions passed:

- `stage = RAW_DISCOVERY_LEDGER_ONLY`
- `primary_tests = 820`
- `discovery_source_slots = 480`
- `confirmation_2025_accessed = false`
- `confirmation_2025_files_opened = 0`
- `access_2026_plus = false`
- `costs_applied = false`
- `multiple_testing_applied = false`
- `scout_score_applied = false`
- derived daily SHA256 = `b92741d682a704a237cc1ab1a4d1fb0beb13798b11993ddde9ef54bcd4f3ab20`

No new per-cell performance metric, survivor ranking, re-routing result, 2025 outcome, or 2026+ market outcome was inspected before freezing this addendum. The historical 1D final-freeze summary and the identities of the three historical survivors were already immutable prior evidence.

## 2. Prospective authority reused

This addendum adopts the operational incomplete-boundary-week rule already frozen prospectively in:

**CED-4H-V1 — PRE-DISCOVERY AMENDMENT 01 — V0.1**  
Google Drive ID: `1i06x1R1iFerQYEtKSoJvhD9ONtR6y_qx-j1k8Uj_79w`

That document states `FROZEN BEFORE ANY 4H MARKET STATISTICS` and resolved the same split-edge incomplete-UTC-week problem before 4H outcomes. This V3 1D addendum does not invent a favorable post-outcome treatment; it imports that already-prospective operational rule for the same weekly-bootstrap boundary condition.

## 3. Frozen boundary-week rule

- UTC week = Monday 00:00 UTC inclusive to the next Monday 00:00 UTC exclusive.
- Week anchor = **signal completion timestamp**.
- Full Discovery ledger window remains 2021-01-01T00:00:00Z through 2025-01-01T00:00:00Z, end-exclusive.
- Complete-UTC-week inference window is 2021-01-04T00:00:00Z inclusive through 2024-12-30T00:00:00Z exclusive.
- All Discovery signals/events remain in the immutable ledger, including partial split-edge UTC weeks.
- Partial-boundary-week rows are marked `inference_week_eligible=false` / `BOUNDARY_WEEK_LEDGER_ONLY`.
- A row is not relabelled `DATA_UNAVAILABLE` solely because its UTC week is incomplete.
- Only inference-week-eligible events may enter:
  - sample gates;
  - cost aggregation;
  - temporal/stability/concentration metrics;
  - bootstrap;
  - BH/multiple-testing diagnostics;
  - Scout Score;
  - V3 survivor routing/re-adjudication.
- Any event requiring entry, exit, or path data outside Discovery remains `DATA_UNAVAILABLE` under the original temporal firewall.
- 2025 Confirmation remains unopened.
- 2026+ remains forbidden.

## 4. Exact frozen survivor population

No new cell may be admitted. Re-adjudication is limited to:

1. AVAXUSDT — Momentum 20D — CONTINUATION — hold 1D
2. SOLUSDT — Momentum 20D — CONTINUATION — hold 1D
3. SOLUSDT — Momentum 60D — CONTINUATION — hold 1D

No sign, lookback, hold, asset, cost model, event filter, or parameter neighbour may be changed to rescue a result.

## 5. Historical verdict preservation

The historical 1D final freeze remains immutable. Any V3 output must carry:

**HISTORICAL VERDICT PRESERVED / RE-ADJUDICATED UNDER PROMOTION POLICY V3.**

This addendum may remove only the technical inference blocker created by incomplete split-edge weeks. It cannot rewrite the historical ledger, create independence, manufacture a new strategy, or access protected Confirmation data.

## 6. Stop / next gate

First re-adjudicate exactly the three frozen survivors under the boundary rule above using the frozen V0.2 numeric/statistical governance. Only if an exact survivor remains eligible may a separate 2025 Confirmation protocol be written and frozen. Funding/cost provenance must be resolved before any funded Confirmation claim. No 2025 market outcome may be opened merely by this addendum.
