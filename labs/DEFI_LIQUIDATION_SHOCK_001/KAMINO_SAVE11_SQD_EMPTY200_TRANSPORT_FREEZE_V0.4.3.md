# DEFI-LIQUIDATION-SHOCK-001 — SQD EMPTY-200 TRANSPORT HARDENING V0.4.3

Date: 2026-09-24
Status: PREPARED / NOT YET AUTHORITATIVE / TECHNICAL SUPERSESSION ONLY / SOURCE-ONLY / OUTCOME-BLIND

Observed V0.4.2 blocker:
- SQD finalized-stream may return HTTP 200 with an empty body for a valid bounded request.
- Example: Kamino UTC day 2023-11-23 in run 35921229252.
- Prior completed days in the same partition produced 24 successful reference instructions, 62 failed attempts, and zero source anomalies before the transport block.
- Therefore this is transport behavior only. It is not NO_EDGE and not a scientific contradiction.

Scientific contract remains unchanged:
- same Kamino and Save11 programs and instruction identities;
- same authoritative start timestamps/slots;
- same [start, 2025-01-01T00:00:00Z) populations;
- same one-UTC-day logical chunks;
- same +16-slot transport envelope with exact local UTC timestamp filtering;
- same success/failure semantics, deduplication, completeness requirements and deterministic RAW sample;
- same outcome firewalls.

V0.4.3 transport-only change:
- an HTTP 200 response with zero non-empty NDJSON lines is retried for the exact same request up to 6 times;
- exponential backoff: 2, 4, 8, 16, 32, 60 seconds maximum;
- request bounds, filters and fields are byte-for-byte semantically unchanged across retries;
- if all empty-200 retries are exhausted, classify the day SOURCE_CHUNK_BLOCKED and fail closed.

This branch is preparation only. Do not launch while canonical V0.4.2 full census run 35955608980 is active/queued. Use only if that run terminally blocks on the same empty-200 transport class or an equivalent transient SQD response-body absence.
