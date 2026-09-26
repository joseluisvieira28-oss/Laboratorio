# HTF-DH03-12H — SAFE PROGRESS TELEMETRY V0.1 — 2026-09-26

Status: FROZEN TELEMETRY-ONLY / NO SCIENCE CHANGE

Authority ID: `HTF-DH03-12H-SAFE-PROGRESS-TELEMETRY-V0.1`

Parent experiment:
`HTF-DH03-12H-STANDALONE-FORWARD-V1`

## Purpose

Expose non-outcome progress counts from the existing prospective DH03 archive shadow to the canonical Crypto Edge Radar without importing protected strategy outcomes.

The telemetry is operational visibility only. It must not alter, rank, promote, demote, tune, rescue, or adjudicate the candidate.

## Allowed fields

- strategy_id
- schema_version
- source_workflow_run_id
- checked_at_utc
- latest_archive_day
- collector status
- used_as_forward_evidence
- aggregate count of selected forward signals
- aggregate count of price exits
- aggregate count of final resolutions
- aggregate count of funding-pending events
- aggregate count of unresolved price paths
- aggregate count of overlap-skipped events
- explicit safety/firewall booleans

## Forbidden fields

The safe telemetry must contain no:
- symbol-level rows
- signal fingerprints
- timestamps for individual trades
- entry/exit prices
- stops or targets
- funding rates
- gross returns
- net returns
- R multiples
- expectancy
- profit factor
- drawdown
- per-trade outcomes
- parameter changes
- ranking or promotion verdict

## Binding

The telemetry JSON must bind to the exact GitHub Actions `GITHUB_RUN_ID` that produced the source receipt.

The canonical Radar may accept counts only when:
1. the latest successful workflow run id equals `source_workflow_run_id`;
2. the strategy id and schema version match exactly;
3. all explicit outcome/privacy firewalls are false;
4. count fields are non-negative integers;
5. the collector workflow conclusion is success.

If any check fails, counts remain unavailable and the Radar fails closed to metadata-only visibility.

## Workflow transport

The workflow may commit exactly one sanitized file to its own branch:

`crypto_edge_radar/DH03_SAFE_PROGRESS.json`

That path is intentionally excluded from the workflow push trigger so telemetry commits do not recursively trigger the scientific collector.

## Governance

No authenticated exchange API.
No orders.
No exchange mutation.
No wallets.
No live capital.
No science/rule/threshold/cost/timing changes.
No protected outcome import into the Radar.
No automatic promotion.
No main merge.
