# CRYPTO EDGE RADAR — SUPABASE RUNTIME ROLE + SESSION POOLER DISCOVERY V0.1 — 2026-09-27

Status: **FROZEN OPERATIONAL PRE-CUTOVER AUTHORITY / NO SCIENCE CHANGE**

Authority ID: `RADAR-SUPABASE-RUNTIME-ROLE-POOLER-DISCOVERY-V0.1`

## Context

The canonical Render Free Postgres source expires at:
`2026-10-17T08:47:15.2559Z`.

A verified private backup at the 2026-09-27 boundary exists:
- 1032 events;
- 954 event keys;
- chain head `f8b85ba3d45dcb426e37d1a1da543cff61a85d9ea0a01ddc1a07662b9e7c02cd`;
- canonical snapshot SHA256 `6c74bdcf1013b1ab49fdcefd2e046db6471ea2816c6b425f4a6378dda22de9cb`;
- Drive backup file id `1oam9hmileBQbV80C6o0cQUicXfu-vzvZ`.

Supabase target:
- project ref `jqzdvgjeuveiktftyrlz`;
- project name `crypto-edge-radar-evidence-v05`;
- region `eu-central-1`;
- Free plan;
- target exact at the backup boundary;
- target rowset digests equal the independently computed source-backup digests.

The remaining blocker is a legitimate Postgres session connection credential usable by the persistent Render runtime.

## Connection-mode decision

Current Supabase documentation states:
- Free-plan direct Postgres endpoint is IPv6;
- Render is listed as IPv4-incompatible;
- Shared Supavisor Session Pooler is IPv4 and intended for persistent IPv4-only backends;
- the pooler cluster index cannot be inferred from region and must not be guessed as final configuration.

Therefore the canonical target connection mode is frozen as:
**Supavisor Shared Pooler — Session mode — port 5432**.

No paid IPv4 add-on is authorized.

## Dedicated runtime role

A dedicated login role may be created on the Supabase target:
`radar_runtime`.

The role must be:
- LOGIN;
- NOSUPERUSER;
- NOCREATEDB;
- NOCREATEROLE;
- NOREPLICATION;
- NOBYPASSRLS;
- no ownership of evidence tables;
- no DELETE;
- no UPDATE;
- no TRUNCATE;
- no ALTER/DROP;
- no schema CREATE.

Allowed privileges:
- CONNECT on database `postgres`;
- USAGE on schema `public`;
- SELECT, INSERT on `public.radar_events`;
- SELECT, INSERT on `public.radar_event_keys`;
- USAGE, SELECT on `public.radar_events_id_seq`.

RLS note:
the two evidence tables are deny-by-default to Data API roles and initially have no policies. The dedicated Postgres runtime role is not an API role. No RLS bypass privilege is allowed.

To make the least-privilege role usable while preserving RLS, four role-scoped policies are authorized:
- SELECT on radar_events TO radar_runtime USING (true);
- INSERT on radar_events TO radar_runtime WITH CHECK (true);
- SELECT on radar_event_keys TO radar_runtime USING (true);
- INSERT on radar_event_keys TO radar_runtime WITH CHECK (true).

These policies are role-specific. They do not grant or create access for anon, authenticated, PUBLIC, or any other role. Table grants remain separately limited to SELECT/INSERT for radar_runtime.

## EvidenceStore no-DDL mode

The current PostgresEvidenceStore issues CREATE TABLE/INDEX IF NOT EXISTS during initialization.

To preserve least privilege on the target, a new explicit environment gate may be added:

`RADAR_POSTGRES_SCHEMA_PREPROVISIONED=true`

When true:
- no CREATE TABLE;
- no CREATE INDEX;
- no ALTER;
- no DDL;
- initialization performs read-only existence/shape checks for the two required tables and sequence;
- any missing/incompatible object fails closed.

When false or absent, existing source behavior remains byte-for-byte semantically unchanged.

## Session pooler discovery

A one-startup diagnostic may be added, gated by:
`RADAR_SUPABASE_POOLER_PROBE_ON_START=true`.

Required secret/config inputs:
- project ref;
- dedicated role name;
- dedicated role password;
- region.

The probe:
- tests a bounded list of Supavisor cluster indices;
- session mode only, port 5432;
- username format `radar_runtime.<project-ref>`;
- SSL required;
- starts a read-only transaction;
- reads only count / min id / max id / chain head;
- performs no INSERT/UPDATE/DELETE/DDL;
- logs host + success/failure classification only;
- never logs password or full connection URL;
- has no mutable target boundary hardcoded in source;
- requires explicit audited target identity values for event count, key count and chain head;
- fails closed if any expected identity value is missing or invalid;
- accepts a host only when the live target exactly matches the explicitly supplied audited identity;
- host discovery alone does not prove source/target equivalence and cannot authorize cutover.

No final DATABASE_URL switch is authorized by pooler discovery alone.

## Final cutover remains frozen

The existing `RADAR_POSTGRES_CUTOVER_PROTOCOL_V0.1` remains authoritative.

Before final switch:
1. quiesce source writes;
2. final source snapshot;
3. independent verification;
4. exact reconciliation into target;
5. target exact verification;
6. configure canonical target DATABASE_URL secret;
7. deploy;
8. verify target backend / chain continuity;
9. resume prospectively.

## Firewalls

- no scientific rule/signal/threshold/cost/timing changes;
- no outcome changes;
- no live trading;
- no orders;
- no exchange mutation;
- no wallets;
- no capital;
- no paid resource;
- no main merge;
- no password logging;
- no final cutover until the frozen protocol passes.
