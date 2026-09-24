# DEFI-LIQUIDATION-SHOCK-001 — SQD CENSUS TRANSPORT ADDENDUM V0.4.2.1

Date: 2026-09-24
Status: FROZEN TECHNICAL CORRECTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

This addendum changes no scientific population, program ID, instruction discriminator/tag, authoritative date boundary, transaction-success rule, deduplication key, daily chunk identity, deterministic RAW sample rule, or economic firewall.

## Observed operational blocker

Multiple V0.4.2 partitions progressed through valid UTC chunks with zero source anomalies and then terminated with:

`SOURCE_CHUNK_BLOCKED / empty_200_response`.

Example preserved evidence:
- Kamino partition k202311 successfully completed 2023-11-17 through 2023-11-22;
- 2023-11-23 then received HTTP 200 with an empty response body and was classified blocked by the local runner.

## Upstream client semantics

The current official SQD Portal client represents HTTP 200 as a data response and maps an absent stream body to `data: null`. Its stream loop terminates when `res.data` is absent. Therefore, for a bounded finalized query, HTTP 200 with an empty body is a normal stream termination, not by itself a transport error.

HTTP 529/5xx remain retryable transport conditions. The local retry budget is increased to 20 attempts with a 20-second capped exponential backoff, matching the robustness posture of the official client family.

## Corrected local behavior

For each already-frozen bounded UTC chunk:
- HTTP 200 + non-empty NDJSON: parse and continue exactly as before;
- HTTP 200 + empty body: terminate the bounded stream successfully with no additional matches;
- HTTP 204: terminate the bounded stream as no-data;
- malformed non-empty NDJSON: fail closed;
- non-advancing non-empty stream: fail closed;
- linkage / transaction-state / discriminator anomalies: fail closed;
- timestamp-local membership, authoritative-start filtering, and +16-slot transport envelope remain unchanged.

This is transport semantics correction only. It does not convert an absence of events into evidence of edge and cannot produce `NO_EDGE`, `EDGE`, or promotion.

Firewall unchanged:
prices=false; balances=false; token_balances=false; amounts=false; returns=false; pnl=false; direction=false; economic_outcomes=false; protected_2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
