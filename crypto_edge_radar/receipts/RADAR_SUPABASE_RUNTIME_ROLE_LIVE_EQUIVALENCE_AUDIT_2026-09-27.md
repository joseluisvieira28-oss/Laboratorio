# CRYPTO EDGE RADAR — SUPABASE RUNTIME ROLE + LIVE EQUIVALENCE AUDIT — 2026-09-27 12:19 UTC

Status: **PASS / PRE-CUTOVER READINESS ONLY**

This receipt records two independent operational checks performed before any final cutover.

## 1. Canonical source evidence identity

Observed from the canonical Render runtime at 2026-09-27T12:19:42.909537252Z:

- event_count: 1107
- max_event_id: 1107
- key_count: 1029
- chain_head_sha256: `c9ad5818230491d03e006b107a19df6b059a607e2a5b863db8275cf7ad26c136`
- key_binding_sha256: `fb4d7f43760aaafbf046d02203421e56edc36952c26a63782da7a234e82e92f8`
- sequence_last_value: 1107
- sequence_is_called: true
- chain_verified: true
- payloads_exposed: false
- database_mutation: false

## 2. Independently queried Supabase target identity

Target project:
- provider: Supabase
- project: `crypto-edge-radar-evidence-v05`
- project ref: `jqzdvgjeuveiktftyrlz`
- region: `eu-central-1`

Independently queried target values at the same audit boundary:

- event_count: 1107
- max_event_id: 1107
- key_count: 1029
- chain_head_sha256: `c9ad5818230491d03e006b107a19df6b059a607e2a5b863db8275cf7ad26c136`
- key_binding_sha256: `fb4d7f43760aaafbf046d02203421e56edc36952c26a63782da7a234e82e92f8`
- sequence_last_value: 1107
- sequence_is_called: true

Classification:
`SOURCE_TARGET_EXACT_IDENTITY_AT_1107_EVENTS`

This is point-in-time equality only. It does not authorize cutover and will age as the source continues collecting.

## 3. Dedicated runtime role audit

Role:
`radar_runtime`

Observed role attributes:
- LOGIN: true
- SUPERUSER: false
- CREATEDB: false
- CREATEROLE: false
- REPLICATION: false
- BYPASSRLS: false

Database/schema:
- CONNECT on database: true
- USAGE on public schema: true
- CREATE on public schema: false

Table privileges:
- `public.radar_events`: SELECT + INSERT only
- `public.radar_event_keys`: SELECT + INSERT only
- UPDATE: false
- DELETE: false
- TRUNCATE: false

Sequence privileges:
- `public.radar_events_id_seq` USAGE: true
- SELECT: true
- UPDATE: false

RLS:
- enabled on `radar_events`
- enabled on `radar_event_keys`
- SELECT/INSERT policies exist only for `radar_runtime`
- no role bypass

Classification:
`RUNTIME_ROLE_LEAST_PRIVILEGE_PASS`

## 4. Remaining blocker

The canonical runtime still reports:

`TARGET_CONNECTION_CREDENTIAL_NOT_CONFIGURED`

Frozen connection mode:
`SUPAVISOR_SHARED_SESSION_5432_IPV4`

The database password must remain operator-secret and must not enter ChatGPT, GitHub, Google Drive, receipts or logs.

No exact pooler hostname may be guessed or frozen before the audited discovery probe succeeds with the legitimate secret.

## 5. Backup transport cleanup

Temporary startup backup transport has been explicitly forced off at Render:

- `RADAR_BACKUP_LOG_EMIT_ON_START=false`
- `RADAR_BACKUP_JSON_LOG_EMIT_ON_START=false`

No new backup-log headers were observed in recent canonical restarts before this receipt.

## Governance

- science_changed=false
- outcomes_changed=false
- source_database_mutation=false
- target_database_mutation=false during this audit
- orders=false
- exchange_mutation=false
- live_capital=false
- paid_resource=false
- main_merge=false
- automatic_cutover=false
