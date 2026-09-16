# PMD-001 — BLOCK FETCH TRANSPORT AMENDMENT V0.3

Status: RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME
Branch: `pumpfun-migration-direction-v0.1`
Date: 2026-09-16

## Purpose

The public Solana RPC proved capable of returning the required archival blocks, but sequential full `getBlock` calls with `jsonParsed` representation created a practical throughput bottleneck in the deterministic cross-date audit.

Before any economic outcome is opened, PMD-001 therefore freezes a transport-only optimization for a V0.3 collector.

## Frozen changes

V0.3 may:
1. request the exact same required slots through JSON-RPC batch requests instead of one HTTP request per slot;
2. request `getBlock` with `encoding="json"` instead of `encoding="jsonParsed"`;
3. retry a batch item individually when that item returns an RPC error or is absent from the batch response;
4. preserve one canonical result and SHA-256 per requested slot regardless of transport batching.

## Semantic invariants

V0.3 MUST NOT change:
- the frozen 1,012-candidate population;
- the deterministic 20-date cross-date sample;
- the bonding-curve PDA derivation;
- signature pagination rules;
- the `[T0-300s, floor(T0))` safe window;
- same-second quarantine;
- the exact set of unique slots implied by eligible signatures;
- the requirement to fetch every one of those slots with full transaction details;
- signature-to-slot matching;
- `source_complete` or `feature_source_eligible` definitions;
- the >=1,000 Source Gate;
- the >=20-date requirement;
- provider class inside a scientific population;
- economic hypothesis, outcomes, costs, splits or promotion gates.

## Representation equivalence

`encoding="json"` remains a full block transaction representation. It preserves the transaction message/account keys, signatures, compiled outer instructions, metadata, balances, inner instructions and logs required for deterministic later decoding. It avoids RPC-side human-readable parsing overhead but does not authorize dropping transaction fields required by the lab.

Future feature decoding must use the frozen historical Pump program schema where required. The absence of RPC-side `jsonParsed` labels is not missing economic data.

## Batch integrity

For every JSON-RPC batch:
- request IDs must map one-to-one to requested slots;
- duplicate response IDs fail closed;
- unknown response IDs fail closed;
- missing response IDs are individually retried;
- per-item RPC errors are individually retried;
- if individual remediation still fails, that slot fails the mint closed;
- canonical SHA-256 is computed on the final exact block object used by the run;
- UTC retrieval timestamp is preserved for that final object.

Batching changes transport only. It may never change which slot enters the scientific evidence.

## Evidence storage

`BLOCK_EVIDENCE_STORAGE_AMENDMENT_V02.md` remains controlling for persistence:
- deterministic cross-date audit preserves full blocks;
- full 1,012 run may use compact block ledgers plus exact matched transaction bodies.

## Outcome wall

No post-migration price values, returns, labels, PnL, Discovery statistics, Validation statistics or Holdout data may be opened to evaluate or select this transport optimization.

## Governance

- research-only;
- fail-closed;
- no exchange mutation;
- no live orders;
- no main merge;
- no post-outcome tuning;
- no cherry-picking;
- no threshold rescue.
