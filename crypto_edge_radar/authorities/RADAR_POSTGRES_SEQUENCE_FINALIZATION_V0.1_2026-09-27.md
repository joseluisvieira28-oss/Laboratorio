# CRYPTO EDGE RADAR — POSTGRES SEQUENCE FINALIZATION V0.1 — 2026-09-27

Status: **FROZEN PRE-CUTOVER HARDENING / NO CUTOVER AUTHORITY**

Authority ID: `RADAR-POSTGRES-SEQUENCE-FINALIZATION-V0.1`

Parent authorities:
- `RADAR_POSTGRES_CUTOVER_PROTOCOL_V0.1`
- `RADAR_POSTGRES_CUTOVER_PRESEEDED_TARGET_AMENDMENT_V0.2`
- `RADAR_POSTGRES_APPEND_ONLY_PREFIX_RECONCILIATION_V0.1_2026-09-27`

## Purpose

Close the only remaining portability gap after append-only prefix reconciliation.

The reconciliation path preserves exact source event ids. Explicit-id inserts intentionally do not advance the target BIGSERIAL sequence. Therefore a non-zero final delta must not be followed by prospective writes until the sequence is independently finalized to the exact verified source max id.

## Preconditions

Before any sequence mutation, all must pass inside the same target transaction:

1. source snapshot passes the existing full payload/hash/chain/key verification;
2. target event rows equal the full source event rows exactly, field-for-field;
3. target event-key bindings equal the full source bindings exactly;
4. target chain verifies;
5. target canonical snapshot SHA equals the source canonical snapshot SHA;
6. target event ids are contiguous from 1 through source max id;
7. no row mutation is required or permitted by this operation;
8. the target sequence is the only allowed mutable object.

If any check fails:
`TARGET_SEQUENCE_FINALIZATION_FAIL_CLOSED_NO_MUTATION`.

## Dry run

Default/dry-run:
- reads and verifies the complete target;
- reads current sequence last_value/is_called;
- reports whether finalization is required;
- performs zero mutation.

## Apply mode

Apply mode may:
- acquire the same transaction-scoped advisory chain lock used by the canonical EvidenceStore;
- re-read and re-verify full target equality after the lock;
- execute only:
  `setval(pg_get_serial_sequence('radar_events','id'), source_max_id, true)`;
- re-read sequence and full target;
- require target rows/keys/snapshot/chain to remain byte/text exact.

No table row INSERT/UPDATE/DELETE/TRUNCATE is authorized by this operation.

## Success states

If the sequence was already exact:
`TARGET_SEQUENCE_ALREADY_EXACT`.

If apply mode safely changes only the sequence:
`TARGET_SEQUENCE_FINALIZED_EXACT`.

Both remain pre-cutover evidence only. Neither authorizes DATABASE_URL switching.

## Credential boundary

The dedicated runtime role `radar_runtime` intentionally has no sequence UPDATE privilege.

Sequence finalization therefore requires a separate admin-capable target operation/credential. No admin password or URL may be committed, logged, stored in Drive, or exposed in chat.

## Firewalls

- source mutation=false
- evidence row mutation=false
- science change=false
- outcomes change=false
- orders=false
- exchange mutation=false
- live capital=false
- automatic cutover=false
- main merge=false
