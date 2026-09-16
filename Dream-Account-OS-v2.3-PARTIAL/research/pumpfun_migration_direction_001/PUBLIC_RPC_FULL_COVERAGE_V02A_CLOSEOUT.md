# PMD-001 — Public RPC Source Coverage V0.2A Closeout

Date: 2026-09-16
Status: RESEARCH-ONLY / FAIL-CLOSED / OUTCOMES SEALED
Branch: `pumpfun-migration-direction-source-rebuild-v0.2`

## Scope

This closeout records the terminal result of the frozen public-RPC source-coverage route for PMD-001. It does **not** adjudicate economic edge, directional predictability, profitability, or post-migration returns because no outcomes were opened.

## Frozen authority

- Frozen population: 1,012 unique migration candidates across 20 migration dates.
- Frozen source hierarchy after prospective V0.2A amendment: bonding-curve history first; when curve coverage is unresolved or has zero successful signatures in `[T0-300s,T0)`, query mint history as a redundant index; union/deduplicate signatures; admit only successful signatures with `blockTime < T0`.
- Frozen source gates: total >= 1,000; validation >= 200; holdout >= 200; migration dates >= 20.
- Fail closed. No outcome access before source gate PASS.

## Technical correction before canonical execution

The first V0.2A mint-index fallback probe failed for a purely technical reason: DuckDB required the Python module `pytz`, which was missing from the workflow environment. The workflow dependency was corrected only by adding `pytz`. No population, feature definition, time window, split, gate, label, outcome, or economic rule changed.

Corrected 50-row outcome-blind fallback probe completed successfully:

- probe rows: 50
- source windows resolved: 50/50
- curve rows with any 300s activity: 44
- union rows with any 300s activity: 44
- zero-curve cases recovered by mint fallback: 0
- provider errors: 0
- outcomes opened: false

## Canonical full-population execution

Workflow run: `35130803156`
Execution HEAD: `f7cb21c9fb4f67ac5d2497c91767720e90197773`
Workflow: `PMD-001 Public RPC Full Coverage V0.2`

All four source shards completed successfully and the aggregate completed successfully at the technical level.

### Aggregate receipt

- exact frozen population received: 1,012 / 1,012
- unique manifest indices: 1,012
- resolved source windows: 1,012
- unresolved rows: 0
- rows with any successful pre-T0 activity in 300s: **911**
- rows with any successful pre-T0 activity in 60s: **905**
- rows with any successful pre-T0 activity in 30s: **900**
- distinct migration dates represented in 300s activity: **20**
- projected frozen split among 300s-source-valid rows:
  - discovery: **546**
  - validation: **182**
  - holdout: **183**
- outcomes opened: **false**
- forbidden outcome file acquired: **false**
- merged audit SHA-256: `e68340d2b29444fd39260f356508bffe634f82fb5666d668553683f3e5dba0d2`

### Frozen-gate adjudication

| Gate | Frozen minimum | Observed | Result |
|---|---:|---:|---|
| Total 300s source-valid | 1,000 | 911 | FAIL |
| Validation | 200 | 182 | FAIL |
| Holdout | 200 | 183 | FAIL |
| Distinct migration dates | 20 | 20 | PASS |

Canonical machine classification:

`PUBLIC_RPC_SOURCE_COVERAGE_GATE_FAIL_OR_INCOMPLETE`

## Redundant mint-index diagnostic

Population-wide fallback diagnostics:

- total mint fallback queries: 103
- zero-curve cases recovered by mint fallback: 2
- old curve-only census rows with any 300s activity: 909
- V0.2A curve+mint census rows with any 300s activity: 911
- net legitimate recovery: +2 rows

The prospectively authorized redundant index therefore did not provide enough additional source coverage to meet the frozen gate.

## Terminal scientific decision

**STOP the exact public-RPC source route under this frozen authority.**

Not authorized:

- full pre-T0 transaction reconstruction downstream of this failed source gate;
- post-migration outcome acquisition;
- Discovery outcome calculation;
- returns, PnL, directional labels, model fitting, or economic adjudication;
- lowering the 1,000 / 200 / 200 gates after observing the result;
- changing the population or split to rescue the path;
- treating missing source observations as zero demand;
- pooling an alternative sample post hoc to manufacture gate compliance.

This closeout is **not** `NO_EDGE` and is **not** `NEGATIVE_EXPECTANCY`. It establishes that the frozen public-RPC source path does not provide sufficient eligible source coverage for PMD-001 under the precommitted gates. A materially different future source architecture would require a new prospective authority before any outcome access.

## Evidence artifacts

Aggregate artifact:
- artifact ID: `10461014186`
- SHA-256: `13a0cc2ab4853b981e946b4899b94685b71b1dc0fb290ea198c54b6e41f26bf7`

Shard artifacts:
- shard 0: ID `10461902702`, SHA-256 `ca57558276376533244236eb4bcc509dcfaa7ed7ca2d9399c8c0c25f2f49ee1e`
- shard 1: ID `10460834206`, SHA-256 `16f226153310c3104a97ea50d1aa116e44ca04672bc4c4b6b63f5d58a4fa3112`
- shard 2: ID `10460984364`, SHA-256 `19c94e7ffd605e94a6a4cceb3149c8dd566c36376fb519aa8f6a4d07a44f7fc1`
- shard 3: ID `10460913995`, SHA-256 `ea8e20de8270c778038d9048d9cd7747043d1d4cae3dcddcfb2060b6348eba07`
