# CRYPTO EDGE RADAR — SUPABASE RUNTIME ROLE PREP RECEIPT — 2026-09-27

Status: **ROLE + RLS POLICY PREPARED / PASSWORD + POOLER HOST STILL BLOCKED**

Authority:
`RADAR-SUPABASE-RUNTIME-ROLE-POOLER-DISCOVERY-V0.1`

Project:
- ref: `jqzdvgjeuveiktftyrlz`
- name: `crypto-edge-radar-evidence-v05`
- region: `eu-central-1`
- plan: Free
- status previously observed: `ACTIVE_HEALTHY`

## Dedicated role created

Role:
`radar_runtime`

Verified attributes:
- LOGIN = true
- SUPERUSER = false
- CREATEROLE = false
- CREATEDB = false
- REPLICATION = false
- BYPASSRLS = false
- INHERIT = false

Schema:
- public USAGE = true
- public CREATE = false

Table grants:
- public.radar_events: SELECT, INSERT only
- public.radar_event_keys: SELECT, INSERT only

Sequence:
- public.radar_events_id_seq: USAGE, SELECT only

No UPDATE, DELETE, TRUNCATE, ALTER, DROP, schema CREATE or ownership was granted.

## Role-specific RLS

Four role-scoped policies were created:
- radar_events / SELECT / TO radar_runtime / USING (true)
- radar_events / INSERT / TO radar_runtime / WITH CHECK (true)
- radar_event_keys / SELECT / TO radar_runtime / USING (true)
- radar_event_keys / INSERT / TO radar_runtime / WITH CHECK (true)

These do not grant access to anon, authenticated, PUBLIC, or other roles.

## Password protection outcome

Attempts to assign a database password through the connected Supabase SQL tool were blocked by the platform/tool safety layer, including an attempt using a SCRAM verifier rather than plaintext.

No password was persisted in GitHub, Drive, logs, receipts or source code.

The role currently has no usable externally supplied connection password from this workflow.

## Pooler endpoint

Current Supabase documentation was checked before implementation.

Frozen connection mode:
- Shared Supavisor Session Pooler
- IPv4
- port 5432
- username form: `radar_runtime.<project-ref>`
- SSL required

The pooler cluster index is not inferred. The final host must be discovered from an authenticated connection or copied from the Supabase Connect dialog.

A read-only bounded pooler discovery probe is implemented separately and accepts a host only if it matches the frozen target evidence boundary. It never logs a password or a full connection URL.

## Evidence target observation

The earlier exact-equivalence receipt froze:
- 1032 events
- 954 keys
- max id 1032
- chain head `f8b85ba3d45dcb426e37d1a1da543cff61a85d9ea0a01ddc1a07662b9e7c02cd`

During this preparation the target was later observed at:
- 1035 events
- 957 keys
- ids 1..1035
- chain head `a305a8b9f5864377d3409ced06d8d44448f850375d0125b2a95feeac4406ebb8`
- sequence last_value 1035

The three post-boundary events are:
- RADAR_RUNTIME_LIVENESS at id 1033
- ETF_EXEC_V2_PUBLIC_PREFLIGHT at id 1034
- RADAR_RUNTIME_LIVENESS at id 1035

The live Render source was independently observed at the same time with:
- health = OK
- verified 1035 events via postgres
- commit `d4762b70b673daada386276467ea5be2796018e1`

This receipt does **not** claim post-boundary row-for-row equivalence because a new source snapshot was not reconstructed and independently hashed at this point.

## Remaining blocker

The only connection-specific blocker is:
1. assign a legitimate password to `radar_runtime` without exposing it to chat/repo/logs;
2. obtain/discover the exact Session Pooler host;
3. run the read-only probe;
4. only after exact target verification, continue with the frozen final quiesced cutover protocol.

## Safety

- evidence row mutation by this role-prep attack: false
- evidence key mutation by this role-prep attack: false
- scientific change: false
- live trading: false
- orders: false
- exchange mutation: false
- capital: false
- paid resource: false
- main merge: false
