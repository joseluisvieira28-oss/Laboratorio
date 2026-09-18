# STETH-REDEMPTION-BASIS-002 — DISCOVERY RPC 429 TRANSPORT REMEDIATION V0.1A

Date: 2026-09-18
Status: **FROZEN AFTER TECHNICAL FAILURE / BEFORE ANY VALID DISCOVERY OUTCOME**

## Canonical failed execution

Discovery run:
- run: `35387691310`
- head: `6e4e8787a0b0a0043197587e3430e8b5dc6196ee`
- artifact: `10566369698`
- artifact digest: `sha256:350484c0d75290fc37134abdbd304300390d67ce3886113f573b5c7714cdb1e7`
- classification: `DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE`

Exact failure:
`batch RPC item 6 failed: code 429 / compute-units-per-second capacity`.

The run did not produce a scientific Discovery classification.
It did not authorize any parameter change.

## Immutable scientific authority

The following remain unchanged and authoritative:

- FINAL PRE-DISCOVERY PROTOCOL V0.1;
- DISCOVERY IMPLEMENTATION FREEZE V0.1;
- 596 daily 12:00 UTC snapshots;
- 10 ETH notional;
- 2 bps base / 5 bps stress fill haircut;
- 14-day queue horizon;
- compounded trailing 7-day APR implementation:
  `G_7d^(365/7) - 1`;
- next-block rebasing-token request semantics;
- exact checkpoint storage / claim reconstruction;
- moving-block bootstrap:
  - 10,000 replications;
  - seed 20260918;
  - circular blocks;
  - block length `max(2, ceil(n^(1/3)))`;
  - empirical 2.5th percentile lower bound;
- all sample and promotion gates;
- no 2025/2026;
- no post-outcome rescue.

## Authorized transport-only remediation

The only authorized code changes are inside RPC transport batching/retry behavior:

1. split a logical RPC batch into smaller transport chunks;
2. preserve request order and exact returned values;
3. detect JSON-RPC item-level transient errors, including code 429;
4. retry the same exact chunk with deterministic exponential backoff;
5. retain existing HTTP-level retry handling;
6. retain exact 2-of-3 provider quorum;
7. fail closed after finite retry budget.

No block, contract, calldata, timestamp, state field, signal rule, cost, finalization mapping, outcome or statistic may change.

Transport chunk size is frozen at **10 JSON-RPC requests**.
Item-level transient retry budget is frozen at **8 attempts**.
Backoff is deterministic:
`min(20 seconds, 1.5 * 2^attempt)`.

## Supersession / anti-duplication

Any later execution that changes APR annualization, bootstrap family/quantile/block length, queue mechanics, costs, signal definition or pass gates is **not** a valid remediation of run 35387691310 and must not be used for scientific adjudication under this LAB_ID/V0.1.

The next canonical Discovery execution must bind:
- original implementation freeze unchanged;
- this V0.1A transport remediation;
- exact source receipt run 35386033845 / artifact 10563803871.

No valid Discovery outcome existed before this remediation.
