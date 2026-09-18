# CED-1D-V1 — 2025 CONFIRMATION MULTIPLICITY / NEIGHBOUR AMENDMENT — V0.2 — 2026-09-18

**Status:** FROZEN BEFORE 2025 MARKET OUTCOMES  
**Supersedes only Sections 7/8 of:** CED_1D_2025_TRANSFERRED_REPLICATION_CONFIRMATION_FREEZE_V0.1_2026-09-18.md  
**Reason:** canonical V0.2 Confirmation governance requires the union of each finalist and its immediate predeclared grid neighbours to enter the fixed confirmatory multiplicity family. This amendment was frozen before any 2025 return, trade result, p-value, or routing outcome was opened.

## A. Primary target population — unchanged

Only these three cells can become replication survivors:
- CED1D-0031 — AVAXUSDT — 20D CONT — H1D
- CED1D-0241 — SOLUSDT — 20D CONT — H1D
- CED1D-0251 — SOLUSDT — 60D CONT — H1D

No other cell may be promoted or relabelled as a target.

## B. Frozen dependency / confirmatory-variant union

The exact unique 8-cell family is:

1. CED1D-0031 — AVAXUSDT — 20D CONT — H1D — PRIMARY TARGET
2. CED1D-0033 — AVAXUSDT — 20D CONT — H3D — NEIGHBOUR ONLY
3. CED1D-0041 — AVAXUSDT — 60D CONT — H1D — NEIGHBOUR ONLY
4. CED1D-0241 — SOLUSDT — 20D CONT — H1D — PRIMARY TARGET
5. CED1D-0243 — SOLUSDT — 20D CONT — H3D — NEIGHBOUR ONLY
6. CED1D-0251 — SOLUSDT — 60D CONT — H1D — PRIMARY TARGET
7. CED1D-0253 — SOLUSDT — 60D CONT — H3D — NEIGHBOUR ONLY
8. CED1D-0261 — SOLUSDT — 120D CONT — H1D — NEIGHBOUR ONLY

This union is derived mechanically from the already-frozen V0.2 neighbour map and the pre-outcome V3 re-adjudication dependency scope. No outcome was used to choose it.

## C. Multiplicity

Holm FWER 0.05 is computed across all 8 unique cells.

Cells that fail sample or inference gates remain in the Holm denominator with internal p=1 exactly as required by V0.2.

Only the three PRIMARY TARGET cells are adjudicated for replication survival.

## D. Neighbour stability

For each PRIMARY TARGET:
- use only its exact predeclared immediate neighbours above;
- a neighbour qualifies when it passes the applicable sample gate, has positive BASE14 mean, and has BASE14 mean >= 50% of the selected target's BASE14 mean;
- frozen neighbour stability requirement = qualifying neighbour fraction >= 0.75.

Neighbour cells are dependencies only and cannot become new candidates or survivors.

## E. 2025 source scope extension for dependencies

Because the five dependencies use only AVAXUSDT/SOLUSDT and maximum lookback 120D / maximum horizon 3D, the price source remains the same two-symbol official Binance USD-M corpus.

Warm-up must be sufficient for the 120D dependency before the first 2025 signal. Therefore the source manifest is amended prospectively to include:
- 2024-09, 2024-10, 2024-11, 2024-12 for AVAXUSDT and SOLUSDT;
- 2025-01 through 2025-12 for both symbols.

No warm-up event is a 2025 Confirmation observation.

No 2026 price byte may be opened.

## F. Family reporting

The complete vector of all 8 cells must be present in the output.
Only the 3 PRIMARY TARGETS receive an OOS replication verdict.
No losing primary target may be dropped to create a family-level pass.

All other V0.1 governance, costs, funding rules, temporal firewall, stop rule, no-live restrictions, and reference-price execution limitation remain unchanged.
