# UPBIT-KRW-LISTING-SHOCK-001 — WAYBACK GZIP TRANSPORT REMEDIATION V0.2.3A

Date: 2026-09-27
Status: FROZEN BEFORE RETRY / TRANSPORT-ONLY / OUTCOME-BLIND

## Trigger

V0.2.3 replayed the prospectively selected modern Wayback samples successfully with HTTP 200 and content-type application/json, but the returned archived bytes began with gzip magic bytes `1f 8b`.

The Wayback raw replay response did not expose Content-Encoding in a way the V0.2.3 parser used, so UTF-8 decoding failed before JSON parsing.

This is a transport-encoding defect in the audit runner, not a scientific/schema result.

Legacy sample replay also experienced transport connection refusal and remains fail-closed unless the exact same selected samples become readable under this retry.

## Permitted change

For the exact same deterministic sample selection as V0.2.3:
- after replay body acquisition;
- if and only if the first two bytes are `0x1f 0x8b`;
- decompress using the standard gzip format;
- hash and preserve both raw archived bytes and decoded payload bytes;
- parse JSON from the decoded bytes.

If magic bytes are absent, parse the original bytes unchanged.

No Content-Encoding guess other than gzip magic detection.

## Frozen sample selection

Unchanged from V0.2.3:
- earliest and latest exact-list capture per family;
- max 4 archived payloads;
- same CDX query/window/path filters.

No manual sample changes after observing V0.2.3.

## Evidence/output

Same schema-only extraction and event-value firewalls as V0.2.3.

Add only:
- gzip_magic_detected boolean;
- raw_archive_sha256;
- decoded_payload_sha256;
- raw bytes;
- decoded bytes.

Do not emit event titles, IDs or timestamps.

## Scientific effect

None.

V0.2.3's `ARCHIVE_SCHEMA_NOT_EQUIVALENT` is not treated as a valid schema conclusion because parsing never reached JSON for the modern samples.

This retry supplies the first valid schema adjudication if transport succeeds.

No historical enumeration.
No Binance.
No outcomes.
No strategy changes.
No main merge.
