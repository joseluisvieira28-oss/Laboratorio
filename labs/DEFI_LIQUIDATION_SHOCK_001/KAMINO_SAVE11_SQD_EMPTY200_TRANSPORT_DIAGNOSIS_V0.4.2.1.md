# KAMINO + SAVE11 SQD EMPTY-200 TRANSPORT DIAGNOSIS V0.4.2.1

Lab: DEFI-LIQUIDATION-SHOCK-001
Scope: transport/source only
Scientific population: unchanged
Economic outcomes: closed

Observed in full census run 35921229252:
- Kamino 2023-11-23: SOURCE_CHUNK_BLOCKED, stream_complete=false, anomaly_count=0, detail=empty_200_response.
- Save11 2024-07-23: SOURCE_CHUNK_BLOCKED, stream_complete=false, anomaly_count=0, detail=empty_200_response.
- Additional observed examples: Kamino 2024-10-03 and 2024-11-08 with the same transport detail.

Classification:
TECHNICAL_TRANSPORT_BLOCKER — transient HTTP 200 with empty body is not proof of an empty census day and must not be converted into NO_EDGE or SOURCE_PASS.

Required hardening:
Retry the exact same SQD request on HTTP 200 + empty body with bounded deterministic backoff. If retries exhaust, remain fail-closed. Do not alter dates, program IDs, discriminator/tag, success semantics, UTC membership, +16 slot envelope, or RAW sampling rule.

Provenance hardening:
Future authoritative runs should pin checkout to the workflow run SHA rather than a mutable branch name.
