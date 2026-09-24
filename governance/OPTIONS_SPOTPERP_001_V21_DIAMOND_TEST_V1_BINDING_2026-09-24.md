# OPTIONS-SPOTPERP-001 / V2.1 — DIAMOND TEST V1 BINDING — 2026-09-24

Status: FROZEN / PROSPECTIVE ADDITIVE BINDING
Parent authority: OPTIONS-SPOTPERP-001-V2.1-FORWARD-EVIDENCE-GATE-V0.1
Diamond authority: DIAMOND-TEST-V1-FROZEN-2026-09-24
Current state: DIAMOND_TEST_COLLECTING

## No new scientific rule

This binding changes no signal, universe, direction, execution horizon, RV state, weight, cost, asset or source rule.

The existing first-50 forward gate remains the decisive statistical gate:

- exactly first 50 resolved forward trades chronologically;
- BASE10 mean > 0;
- BASE10 PF > 1;
- five consecutive 10-trade blocks;
- at least 3/5 blocks non-negative;
- largest single positive BASE10 trade share <= 40%;
- zero duplicate signal keys;
- zero duplicate resolution keys;
- zero resolution without directional signal;
- STRESS20 remains a mandatory fragility diagnostic.

## Diamond interpretation

If the frozen first-50 statistical gate fails:
`DIAMOND_TEST_FAIL__EXACT_V21_NO_RESCUE`.

If the frozen first-50 statistical gate passes:
`DIAMOND_TEST_STATISTICAL_LAYER_PASS__OPERATIONAL_REALISM_STILL_REQUIRED`.

A statistical pass alone is not `DIAMOND_TEST_SURVIVES` because the historical 2025 evidence is already cost-fragile: STRESS20 was negative.

Before final Diamond survival, a separate operational-execution audit must establish that the real intended implementation can defend its frozen cost assumptions without lowering costs after outcomes. That audit may not change the first-50 scientific result.

## Falsification

- first 50 BASE10 mean <= 0;
- first 50 PF <= 1;
- fewer than 3/5 non-negative 10-trade blocks;
- concentration > 40%;
- integrity failure;
- future operational evidence shows realistic execution costs incompatible with the frozen positive BASE10 economics.

No rescue by cost reduction, alternate quarter, signal magnitude filter, direction switch, horizon change, or alternative risk cell.
