# ETH-STAKING-FLOW-001 — ARCHIVE TRANSPORT PROBE EXECUTION AMENDMENT V0.3A

Date: 2026-09-18
Status: **FROZEN BEFORE REMEDIATED EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

Parent authority:
`ETH_STAKING_FLOW_001_ARCHIVE_TRANSPORT_PROBE_AUTHORITY_V0_3.md`

## Observed operational failure

Canonical V0.3 run `35335299923` was cancelled at the workflow's explicit 15-minute wall-clock ceiling while still inside the historical boundary transport probe.

No probe receipt was uploaded.
No source classification was reached.
No market outcome was opened.

Classification of that run:
**OPERATIONAL_WALL_CLOCK_CANCELLATION / NO SCIENTIFIC VERDICT**.

## Sole remediation

Execution topology only:

- preserve the exact five providers and their frozen order;
- preserve both boundary dates;
- preserve +0..32 slot search;
- preserve both status filters;
- preserve per-request timeout = 50 seconds;
- preserve schema validation and auth-block semantics;
- execute each provider in an independent GitHub Actions matrix job;
- permit provider jobs to run concurrently;
- canonical aggregate selects the first provider that passes in the ORIGINAL frozen order.

Parallel acquisition does not change provider priority. It only prevents a slow earlier provider from consuming the entire global workflow wall-clock budget before later frozen providers can be tested.

Each provider job receives a 120-minute workflow ceiling.
The aggregate may emit only the existing V0.3 classifications:
- ARCHIVE_TRANSPORT_PROBE_PASS
- ARCHIVE_TRANSPORT_PROBE_BLOCKED
- ARCHIVE_TRANSPORT_PROBE_TECHNICAL_FAILURE
- PROVENANCE_FAILURE

## Unchanged scientific/source semantics

No change to:
- parent MVE ESF-NETQUEUE-7D-001;
- source window 2023-04-12..2024-12-31;
- pending_queued / active_exiting variables;
- first canonical state at/after 00:00 UTC;
- +32 slot maximum;
- source schema;
- later threshold/direction/horizon/costs;
- any promotion gate.

## Firewall

No ETH/BTC prices.
No signal series.
No Discovery event count.
No returns/PnL/performance.
No 2025/2026.
No live trading.
No exchange mutation.
No wallet access.
No merge to main.
