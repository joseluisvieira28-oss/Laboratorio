# BTC-FEE-PRESSURE-001 — SOURCE-REMEDIATION AUTHORITY V0.3

Status: FROZEN PRE-ACQUISITION / OUTCOME-BLIND  
Date: 2026-09-14 UTC  
Lineage: V0.1 DATA_FAILURE; V0.2 SOURCE_ACQUISITION_TECHNICAL_FAILURE_TIMEOUT.  
Scope of change: execution topology only. No scientific rule changes.

## Immutable MVE
BFP-TOTALFEES-7D-001. Daily total BTC transaction fees paid to miners in canonical blocks assigned to UTC day, excluding coinbase reward. Future trigger remains strictly above trailing 90-observation 80th percentile excluding day t. Direction LONG BTC. Entry next UTC daily open after signal. Hold 7 calendar days. Overlapping signals prohibited. Costs 10 bps roundtrip base and 20 bps stress.

## Frozen source window
2021-01-01T00:00:00Z through 2024-12-31T23:59:59Z only.

## Frozen source route
Read-only mempool.space backend:
- GET /api/v1/mining/blocks/timestamp/{unix_timestamp}
- GET /api/v1/blocks/{start_height}

The global boundary heights are resolved only from the two frozen pre-2025 timestamps above. The exact V0.2 request-height sequence is preserved: `range(end_height, start_height - 1, -10)`.

No alternate fee metric, USD fee field, market-price field, current mempool state, fee estimate, exchange API, write endpoint, or protected-period endpoint is authorized.

## V0.3 technical remediation
The exact frozen request-height sequence is partitioned deterministically into four contiguous shards by request-list position. Shards are execution-only partitions; they do not alter source, metric, time window, observations, thresholds, signal, direction, timing, costs or future outcome logic.

Each shard independently resolves and records the same global frozen boundary heights; executes only its assigned subset of the exact V0.2 request-height sequence; preserves raw response bytes, URL, status and SHA256; emits a block identity/index file plus a source-only chunk manifest; and may terminate only as CHUNK_PASS, SOURCE_AUTH_BLOCKED, SOURCE_ACQUISITION_TECHNICAL_FAILURE, DATA_FAILURE or PROVENANCE_FAILURE.

The merge requires exactly four CHUNK_PASS artifacts; identical global boundaries across shards; exact reconstruction of the full frozen request-height sequence; no missing, duplicated or foreign request heights; fail-closed block-height/hash reconciliation; all heights from global start through global end present; no conflicting hashes; finite non-negative fees; UTC assignment inside 2021-2024; no fill/interpolation; and at least 1,400 UTC daily observations.

Final valid terminal states remain SOURCE_DATA_PASS, SOURCE_AUTH_BLOCKED, SOURCE_ACQUISITION_TECHNICAL_FAILURE, DATA_FAILURE, PROVENANCE_FAILURE, INSUFFICIENT_SAMPLE.

## Firewalls
Discovery prohibited. BTC prices, ETH prices, returns, PnL and performance statistics prohibited. 2025 and 2026 prohibited. Live trading and exchange mutation prohibited. No merge to main and no deployment authorized.

A SOURCE_DATA_PASS authorizes only a later request for explicit Discovery authorization; it does not itself authorize outcomes.

Drive authority receipt: `1SetlZMVpXCpXdtF9NfRT4fhP3oswKVZq08eF3yE-Td4`.
