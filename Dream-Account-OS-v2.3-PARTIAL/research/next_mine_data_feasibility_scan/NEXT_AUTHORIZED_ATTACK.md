# RECOMMENDED NEXT ATTACK — DATA BASIS ONLY

Candidate: `STETH-REDEMPTION-BASIS-002`  
Status: `DATA_READY_WITH_CONTROLS`  
Primary source: Ethereum mainnet historical contract state via frozen public archive-RPC
quorum; bounded canonical event logs via SQD Ethereum-mainnet Portal  
Historical coverage: 2023-05-16T12:00:00Z through 2024-12-31T12:00:00Z, 596 frozen daily snapshots

## Why source passes

- `SOURCE_DATA_PASS` was established before economic outcomes.
- The start boundary is derived from the canonical Lido V2 activation transaction/block,
  not from performance or source convenience.
- Historical state and timestamp-to-block mapping require agreement from at least two of
  three frozen providers.
- Exact contract addresses, event signatures, daily clock and terminal boundary are frozen.
- SQD acquisition is bounded by block range and supports deterministic pagination.
- Raw responses, canonical event identities and receipts can be preserved and SHA-256 hashed.
- Ethereum block/log history supports point-in-time reconstruction without a current-state
  backfill.

## Main controls required

Provider quorum, pinned block hashes, raw-byte retention, request/response receipts, SQD
pagination/gap checks, strict 2024 ceiling, retry-only transport remediation, exact binding to
the frozen source receipt and implementation, and canonical-run precedence.

## Duplication status

`DISTINCT`. This is protocol-redemption convergence after canonical Lido V2 activation. It
does not reopen `STETH-REDEMPTION-BASIS-001` and is not validator-flow or stablecoin-peg work.

## What must be frozen before outcomes

Already frozen: source population, snapshot clock, contracts, predictor construction,
redemption/queue semantics, costs, one-position rule, sample gates and classification rules.
Before execution, record the exact Git commit, source receipt hash, protocol hash, code hash,
provider list and output schema. Verify that no admissible canonical closeout already exists.

## Smallest next experiment

Execute exactly one canonical transport-remediated Discovery from the frozen 596-snapshot
population. Stop as `TECHNICAL_FAILURE` or `PROVENANCE_FAILURE` if acquisition/binding fails.
Do not read or compare outcomes from noncanonical retries.

## What remains prohibited

No parameter/source-clock/window change, no source substitution after outcomes, no 2025/2026,
no protected-data opening outside the frozen protocol, no live trading, no wallet, no order,
no exchange mutation, no paid data/trial and no merge to `main`.
