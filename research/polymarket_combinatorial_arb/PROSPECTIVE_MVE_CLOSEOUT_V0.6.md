# POLY-COMBINATORIAL-ARB-001 — PROSPECTIVE MVE CLOSEOUT V0.6

Date: 2026-09-27
Status: PILOT_DATA_INSUFFICIENT / EXECUTION-PROVENANCE BLOCKED / NOT NO_EDGE
Branch: prediction-combinatorial-arb-v0.6-prospective-mve

## Canonical run
Workflow: POLY-COMB Prospective MVE V0.6
Run ID: 36333605590
Job ID: 108660119290
Conclusion: SUCCESS
Freeze/runtime commit: 0a2d37f97a0a0695cc3af67aa877761b755a21c1
Artifact ID: 10936373069
Artifact ZIP SHA256: 614060b528914646dd895f835163a5237c56774ca9b95a7e05316144208b918a

## Frozen prospective protocol
- BUY_ALL_YES only.
- q = 10 YES shares per component outcome.
- visible ask-depth walk only.
- fixed provider timestamp-dispersion gate <= 2000 ms.
- economics computed only if every token fee state was explicitly proven zero.
- fixed package buffers: 0.05 USDC BASE / 0.10 USDC STRESS.
- exactly 60 attempts at 2-second cadence.
- no extension/backfill.

## Result
Pilot adjudication: PILOT_DATA_INSUFFICIENT.

- 60/60 scheduled attempts completed.
- valid economic event-snapshots: 0.
- package margins computed: 0.
- positive stress observations: 0.
- scientific edge verdict: NONE.

Per-event blocking evidence:
- 32228: max provider timestamp dispersion 19,749 ms; 0 valid economic snapshots.
- 48292: max provider timestamp dispersion 224,607 ms; 0 valid economic snapshots.
- 51456: max provider timestamp dispersion 55,553 ms; 0 valid economic snapshots.

Fee gate:
- every frozen token returned a non-zero /fee-rate base_fee representation.
- V0.6 deliberately refused to infer the effective fee formula or convert that representation into economics.
- therefore fee_all_zero=false on all three events.

## Safety
PASS:
- authenticated endpoints = false;
- orders = false;
- capital = false;
- exchange mutation = false;
- no midpoint economics;
- no post-outcome threshold adjustment;
- no main merge.

## Scientific interpretation
V0.6 did NOT show "no arbitrage".
It showed that the exact V0.6 execution-provenance gate was too unresolved to open package economics.

The two blockers are distinct:
1. FEE_PROVENANCE: current fee representation/formula must be established from the active first-party client/market metadata.
2. BOOK_TIME_SEMANTICS: provider book timestamps differ materially across legs even when books are fetched in one batch; their meaning must be established before they are used as a synchronization test.

## No-retroactive-rescue rule
V0.6 snapshots are closed.
No later fee formula or timestamp interpretation may be applied retroactively to V0.6 to manufacture an economic result.

Any remediation must be SOURCE-ONLY under a new version, followed by a separately frozen prospective economic MVE.

