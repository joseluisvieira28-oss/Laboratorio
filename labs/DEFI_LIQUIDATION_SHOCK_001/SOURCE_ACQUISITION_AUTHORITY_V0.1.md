# DEFI-LIQUIDATION-SHOCK-001 — SOURCE ACQUISITION AUTHORITY V0.1

Status: RESEARCH-ONLY / OUTCOME-BLIND / READ-ONLY / FAIL-CLOSED

## Why this authority exists

`SOURCE_DATA_GATE_RECEIPT_V0.2` established that the uploaded Helius/MSEL corpus is a Pump.fun/memecoin corpus, not a protocol-wide DeFi liquidation corpus. That result is `SOURCE_DATA_INSUFFICIENT / CORPUS_DOMAIN_MISMATCH`, not `NO_EDGE`.

This authority prospectively defines the smallest valid source-acquisition route for the missing DeFi liquidation event population. It does not authorize market prices, returns, PnL, directional testing, execution testing, 2025/2026 market outcomes, live trading, exchange mutation, deployment, alerts/webhooks, or merge to main.

## Historical source window

Frozen source-event census window:

- start: `2021-01-01T00:00:00Z`
- end: `2024-12-31T23:59:59Z`

Reason: maximize the pre-protected historical Solana window explicitly permitted by the handoff, without inspecting any future market response. Protocols that did not yet exist simply contribute no events before deployment; their dates must not be backfilled or shifted because of outcomes.

## Candidate protocol universe

The source census begins with the protocol families named prospectively in the handoff and supported by public program/instruction evidence:

1. Save / Solend lending
2. marginfi v2 lending
3. Kamino Lend
4. Drift v2 liquidation flows

No protocol is a winner. All remain candidates until raw historical availability and decoder validity are proven. Additional protocol IDs may be added only by a new source-authority amendment based on source/mechanism evidence, never on returns.

## Primary source authority

Primary scientific authority must be raw/full Solana transaction evidence from an archival read-only RPC route.

Preferred no-paid route:

1. standard `getSignaturesForAddress(program_id)` pagination to identify candidate transactions;
2. discard out-of-window records before any full-transaction fetch;
3. standard archival `getTransaction` for successful 2021–2024 candidates;
4. preserve exact JSON-RPC response bytes and SHA-256;
5. normalize transaction/slot/blockTime/instruction position/program/data/account references into derived records;
6. decode liquidation instructions only against a historical decoder definition that is pinned by repository commit / IDL / source hash.

This reuses the already-governed MSEL free-tier archival pattern: standard Solana archival RPC reads may be used instead of Helius-only paid `getTransactionsForAddress`.

## Secondary index sources

Dune, Flipside or protocol APIs may be used only as a candidate-signature index or reconciliation source unless their historical completeness, semantics and point-in-time fields are independently proven.

Enriched fields such as USD value, current token metadata, post-event prices or derived labels are not source authority for the event census.

If a secondary index requires a paid plan, trial, purchased dataset or billable query service, stop and request user authorization before using it.

## Historical decoder rule

Current program code is not automatically historical truth.

Before a protocol's decoded liquidations become authoritative, prove for the relevant historical interval:

- program ID / deployment lineage;
- exact liquidation instruction discriminator or native enum tag;
- account ordering / semantics;
- instruction version changes;
- CPI/inner-instruction handling;
- success/failure semantics.

Known current/reference decoder evidence may be recorded as `REFERENCE_ONLY` until historical applicability is proven.

## Transaction inclusion

Candidate transaction:

- signature returned for the protocol program address;
- blockTime inside the frozen 2021–2024 window;
- transaction retrievable in full from the archival source.

Authoritative liquidation event additionally requires:

- transaction `meta.err == null`;
- direct or inner instruction invokes the historically valid protocol program;
- instruction bytes match the historically valid liquidation instruction definition;
- deterministic transaction/instruction position;
- enough account references to identify the obligation/borrower/liquidator/reserves or explicitly mark fields unavailable.

Failed transactions remain source evidence but cannot count as completed liquidation events.

## Protection against pseudo-edge

The collector/decoder must not:

- query any market-price endpoint;
- compute returns or PnL;
- use a post-event price to size an event;
- select only large liquidations before a prospectively frozen size rule exists;
- select a protocol because it later performs better;
- silently deduplicate separate instructions or split one cascade into independent shocks;
- infer missing historical instruction semantics from current code without proof;
- discard inconvenient valid events.

Clustering, notional reconstruction and market mapping remain unfrozen until the raw census is known.

## Raw evidence policy

For every RPC response retained as scientific evidence:

- keep exact response bytes;
- record response SHA-256;
- record request method/parameters hash;
- never call canonicalized/normalized JSON “raw HTTP”;
- derived files receive independent SHA-256 hashes.

## Credit / scale rule

A free archival RPC route is preferred, but full program histories can be large. Hitting a free-tier credit/rate limit produces `SOURCE_ACCESS_BLOCKED` or `SOURCE_ACQUISITION_PARTIAL`, never an edge verdict.

Do not silently switch to a paid route. Do not infer population size from a capped partial run.

## Source Gate promotion criteria

`SOURCE_DATA_PASS` requires, before outcomes:

1. complete or demonstrably coverage-complete historical source route for the frozen protocol universe/window;
2. historical decoder validity for every protocol included in the event population;
3. deterministic deduplication at transaction + instruction identity;
4. successful-vs-failed separation;
5. event field coverage report;
6. liquidation event count and calendar distribution;
7. explicit missing-data report;
8. all raw/derived hashes and run metadata.

Only after this pass may a numerical sample gate, clustering rule and FINAL PRE-DISCOVERY AUTHORITY be frozen.

## Current execution state

The acquisition design is ready, but the connected research runtime currently exposes no archival Solana RPC URL/API credential. That is a technical execution dependency, not evidence against the mechanism and not a request for paid data.

No economic Discovery is authorized by this document.
