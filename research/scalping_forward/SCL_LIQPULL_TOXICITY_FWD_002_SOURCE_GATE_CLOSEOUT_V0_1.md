# SCL-LIQPULL-TOXICITY-FWD-002 — HYBRID SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-25
Status: SOURCE_FEASIBILITY_BLOCKED
Scientific edge verdict: NOT TESTED / NOT NO_EDGE

## Frozen source gate
V002 tested:
- public Hyperliquid REST l2Book BTC at 4 Hz;
- public Hyperliquid WebSocket bbo BTC + trades BTC;
- 120-second source-only probe;
- zero strategy outcomes.

GitHub Actions run: 36188798658
Artifact ID: 10887428971
Artifact ZIP SHA256: 4fa16af1f1559dce784319ee08118aedcc9cc9268763f64dfd0c88bfa364de01

## Frozen gate result
REST:
- target polls: 480
- successful responses: 480
- HTTP errors: 0
- transport errors: 0
- schema errors: 0
- median inter-response gap: 249 ms
- p95 inter-response gap: 364.5 ms
- p95 absolute provider staleness: 855.1 ms
- provider timestamp non-decreasing: FAIL

WebSocket:
- bbo messages: 721
- trade messages: 200
- subscription acknowledgements: PASS
- parse errors: 0
- reconnects: 0

Formal V002 classification:
SOURCE_FEASIBILITY_BLOCKED

## Outcome-blind timestamp postmortem
A source-only inspection of provider timestamps was permitted because it did not inspect price, size, return, markout, PnL, signal, or strategy outcome.

Across 480 accepted HTTP 200 book responses:
- timestamp transitions: 479
- negative transitions: 2
- negative-transition fraction: 0.4175%
- regressions observed: -68 ms and -56 ms
- zero provider-time steps: 256
- positive provider-time steps: 221

No price values were summarized or used.

## Governance consequence
V002 remains closed under its exact frozen requirement of 100% non-decreasing provider timestamps.

Do not reinterpret V002 as PASS.
Do not silently relax the gate.
Do not run any markout/economic evaluator on V002 source-probe data.

The broad passive-fill toxicity mechanism remains scientifically untested.

## New-measurement successor
A new LAB_ID may prospectively define a fail-closed freshness filter:
- accept a REST L2 snapshot only when provider_time >= last accepted provider_time;
- discard stale-regressing responses;
- require the post-filter accepted stream itself to retain frozen cadence/staleness coverage.

That successor inherits zero promotion credit and must pass a new source-only gate before any outcomes.
