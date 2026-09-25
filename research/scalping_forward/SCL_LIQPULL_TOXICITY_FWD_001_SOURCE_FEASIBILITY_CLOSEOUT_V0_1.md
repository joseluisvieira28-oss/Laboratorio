# SCL-LIQPULL-TOXICITY-FWD-001 — SOURCE FEASIBILITY CLOSEOUT V0.1

Date: 2026-09-25
Status: SOURCE_FEASIBILITY_BLOCKED / EXACT V001 SOURCE CONTRACT CLOSED
Scientific edge verdict: NOT TESTED / NOT NO_EDGE

## Frozen source contract
V001 froze public Hyperliquid BTC WebSocket subscriptions only:
- l2Book
- trades

The scientific MVE required a 1,000 ms pre-entry liquidity-pull window and first book snapshot at/after each integer UTC second.

No markout, return, PnL, PF, Sharpe, win rate, slope, quartile outcome, fee-adjusted result, or trading signal was opened under V001.

## Source-only evidence

### 30-second schema smoke
GitHub Actions run: 36187712815
- raw messages: 27
- reconnects: 0
- parse errors: 0
- source: public Hyperliquid mainnet WebSocket
- authenticated endpoint: false
- orders: false
- exchange mutation: false
- outcomes computed: false
- artifact ID: 10886333676
- artifact ZIP SHA256: 1eab30fc510de030f0bf38f9681cafa003c249149fd88f9c37ca41f0e2375c28

### 120-second cadence probe
GitHub Actions run: 36188207874
Artifact ID: 10886703631
Artifact ZIP SHA256: 92b3738de98bcbd2995c0d17d33e9b2dba8a6145c350d64e8f1eb9f8b9ce2102

Observed source timing only:
- l2Book snapshots: 23
- l2 inter-snapshot gaps: 22
- minimum gap: 2,728 ms
- median gap: 5,352.5 ms
- maximum gap: 5,554 ms
- fraction of gaps <=1,500 ms: 0.0
- trade messages: 104
- prices accessed by cadence report: false
- markouts computed: false
- PnL computed: false

## Adjudication

The exact V001 WebSocket-only source route cannot support the frozen 1,000 ms pre-entry depth-change measurement with adequate temporal fidelity.

Classification:
SOURCE_FEASIBILITY_BLOCKED

This is not NO_EDGE and does not falsify the passive adverse-selection / liquidity-withdrawal mechanism.

## Governance consequence

Do not:
- widen the 1,000 ms window;
- change the frozen sampling clock;
- infer missing L2 states;
- interpolate depth;
- use the sparse WebSocket snapshots as if they were 1-second observations;
- run the V001 evaluator on these source-smoke files;
- rescue V001 by silently changing source transport.

Under Governance V4, a materially different measurement/source contract requires a new LAB_ID.

## Objective reopening trigger

V001 may reopen only if the exact public Hyperliquid WebSocket l2Book route itself begins to provide temporal coverage compatible with the unchanged 1,000 ms source contract and this is proven by a new outcome-blind source-only cadence probe.

## Successor route

A successor may test the same broad economic mechanism with a new immutable identity and zero inherited promotion credit using a prospectively frozen high-cadence public read-only L2 source, subject to its own source feasibility gate before any outcomes.
