# CRYPTO EDGE RADAR — APPEND-ONLY PREFIX RECONCILIATION V0.1 — 2026-09-27

Status: **FROZEN PRE-CUTOVER PORTABILITY HARDENING / NO CUTOVER AUTHORITY**

Authority ID: `RADAR-POSTGRES-APPEND-ONLY-PREFIX-RECONCILIATION-V0.1`

## Problem

The existing `restore_snapshot()` portability path requires an empty target.

The Supabase target is already seeded and has continued to receive a small append-only delta. Therefore the final quiesced cutover needs a safe reconciliation path for a **non-empty exact-prefix target**.

## Allowed behavior

A verified source snapshot may be compared against a non-empty target.

The target is eligible only if all are true before any write:
1. source snapshot passes the existing payload/hash/chain/key verification;
2. target event chain independently verifies;
3. target events are an exact ordered prefix of source events, field-for-field:
   - id
   - event_ts
   - event_type
   - payload_json exact text
   - payload_sha256
   - prev_chain_sha256
   - chain_sha256
4. target event-key rows equal exactly the source event-key bindings whose event_id is inside the target prefix;
5. target ids are contiguous from 1 through target max id;
6. target sequence last_value equals target max id before reconciliation;
7. source missing ids after the prefix are contiguous.

If any condition fails: **FAIL CLOSED, ZERO TARGET ROW MUTATION**.

## Existing write-quiescence mechanism

The canonical Radar already exposes:
`RADAR_EVIDENCE_WRITES_QUIESCED=true`.

In this mode `serve_forward_shadow()`:
- verifies the current evidence chain;
- sets mode `EVIDENCE_WRITES_QUIESCED`;
- does not call the normal forward `run_cycle()`;
- does not start the ETF exact-timing scheduler thread;
- does not start the forward-shadow watcher thread;
- can still emit the explicitly enabled private backup snapshot.

A dedicated regression test is part of this hardening and must prove no scientific worker/thread starts while quiesced.

## Apply mode

Apply mode may:
- INSERT only the missing source events;
- preserve the exact source event ids explicitly;
- INSERT only the missing source event-key bindings;
- perform all row inserts in one transaction;
- re-read and verify the resulting target snapshot before commit.

Apply mode must not:
- UPDATE existing evidence rows;
- DELETE;
- TRUNCATE;
- rewrite payload_json;
- reorder events;
- regenerate hashes;
- use UPSERT to hide divergence;
- mutate source;
- change scientific state.

## Sequence boundary

Explicit-id inserts intentionally do not advance the BIGSERIAL sequence.

Therefore a successful non-zero delta reconciliation returns:
`TARGET_DELTA_ROWS_VERIFIED__SEQUENCE_FINALIZATION_REQUIRED`.

That state is **not cutover-ready**.

After row reconciliation, an independently authorized/admin-capable operation must set the target sequence to the verified source max id and re-check:
- sequence last_value = source max id;
- full target snapshot exact;
- chain head exact.

Only then can the existing frozen cutover protocol proceed to DATABASE_URL switch.

## Firewalls

- default / dry-run = read-only;
- no source mutation;
- no science changes;
- no outcomes changes;
- no orders;
- no exchange mutation;
- no capital;
- no automatic DATABASE_URL switch;
- no automatic promotion;
- no main merge.
