# CRYPTO EDGE RADAR — SUPABASE CUTOVER PREFLIGHT BLOCKER RECEIPT — 2026-09-27

Status: **PRE-CUTOVER DRY RUN PASS / OPERATOR SECRET REQUIRED / NO CUTOVER PERFORMED**

Classification: `PRE_CUTOVER_DRY_RUN_PASS__BLOCKED_ON_OPERATOR_SECRET`

## Authority and safety

This receipt records an operational persistence audit only.

- science_changed = false
- outcomes_changed = false
- source_database_mutation = false
- target_evidence_row_mutation = false
- orders = false
- exchange_mutation = false
- live_capital = false
- paid_resource = false
- main_merge = false
- secret_value_exposed = false
- final_cutover_performed = false

## Canonical runtime

Observed canonical branch:
`crypto-edge-radar-postgres-v0.5`

Observed branch HEAD:
`03f0858430fb9aa768410cecc5e8942c970fd4e3`

Observed Render service:
`crypto-edge-radar-v05-canary`
(`srv-dalqkpu1egvs73fhiehg`)

Observed live deploy:
`dep-dash7hbncjis73a4lvlg`

Deployment classification:
`IN_SYNC`

Runtime database target mode:
`SOURCE`

Runtime health:
`OK`

## Source identity — point-in-time observation

Observed runtime boundary:
`2026-09-27T13:30:05.887000Z`

- event_count = 1114
- key_count = 1036
- max_event_id = 1114
- chain_head_sha256 = `5c93c97a38086e4ca848b0103a4d7830cd938e7b45b30bcc127ce17fc136226c`
- key_binding_sha256 = `7c9a41d00a2734a73dcdb19490c1ac2263728f2d880712fbb2bce77a906b4e81`
- sequence_last_value = 1114
- sequence_is_called = true
- chain_verified = true
- evidence backend = postgres

Direct hosted-MCP querying of the Render Postgres source was not opened because the source IP allowlist is intentionally empty. No allowlist mutation was performed. Source identity above was emitted by the canonical runtime from its internal database connection.

## Supabase target — independent verification

Project:
`crypto-edge-radar-evidence-v05`

Project ref:
`jqzdvgjeuveiktftyrlz`

Region:
`eu-central-1`

Status:
`ACTIVE_HEALTHY`

Independent target SQL at the same observed boundary:

- event_count = 1114
- min_id = 1
- max_id = 1114
- distinct_ids = 1114
- noncontiguous_id_count = 0
- key_count = 1036
- payload_sha_mismatch_count = 0
- prev_chain_mismatch_count = 0
- chain_sha_mismatch_count = 0
- orphan_key_count = 0
- chain_head_sha256 = `5c93c97a38086e4ca848b0103a4d7830cd938e7b45b30bcc127ce17fc136226c`
- key_binding_sha256 = `7c9a41d00a2734a73dcdb19490c1ac2263728f2d880712fbb2bce77a906b4e81`
- sequence_last_value = 1114
- sequence_is_called = true

Point-in-time classification:
`SOURCE_TARGET_IDENTITY_EXACT_AT_1114_BOUNDARY`

This observation is not final cutover authority because the source remains prospectively active until final write quiescence.

## Target security / compatibility

Dedicated runtime role:
`radar_runtime`

Observed attributes:
- LOGIN = true
- SUPERUSER = false
- CREATEDB = false
- CREATEROLE = false
- REPLICATION = false
- BYPASSRLS = false

Observed table privileges are limited to:
- SELECT + INSERT on `public.radar_events`
- SELECT + INSERT on `public.radar_event_keys`

Observed additional checks:
- database CONNECT = true
- public schema USAGE = true
- public schema CREATE = false
- sequence USAGE = true
- sequence SELECT = true
- sequence UPDATE = false

RLS policies are role-scoped to `radar_runtime` for SELECT/INSERT on both evidence tables.

Supabase security advisor:
`PASS — 0 lints`

Supabase performance advisor:
`PASS — 0 lints`

Schema, primary keys, foreign key, unique chain hash, sequence and append-only runtime semantics are compatible with the frozen PostgresEvidenceStore preprovisioned/no-DDL target mode.

## Backup transport

No `RADAR_BACKUP` chunk emission was observed in the latest live-deploy window audited from 2026-09-27T13:00:00Z through 2026-09-27T13:35:00Z.

The temporary backup log transport is therefore not being observed as active. No backup transport mutation was performed in this audit.

## Exact blocker

Canonical runtime reports:

- `cutover_blocker = TARGET_CONNECTION_CREDENTIAL_NOT_CONFIGURED`
- `target_connection_preflight.classification = AUTH_REQUIRED_NOT_EXECUTED`
- `target_url_configured = false`
- `target_pooler_host_discovered = false`
- `database_url_switch_authorized = false`

Independent Supabase role inspection additionally proves:

`radar_runtime password_set = false`

Therefore no legitimate password exists to hand to the Render runtime.

The password must not be invented by automation, committed, logged, stored in Drive, or pasted into ChatGPT.

## Minimal operator action required

Privately create a strong password for `radar_runtime` in the Supabase Dashboard SQL Editor, then place that same value directly into the canonical Render service as the secret environment variable:

`RADAR_SUPABASE_POOLER_PASSWORD`

Do not paste the password into chat.
Do not set `RADAR_USE_SUPABASE_TARGET=true`.
Do not remove the existing source database configuration.

After this secret is present, the already-audited read-only Supavisor Session Pooler discovery/preflight can run against a fresh source/target identity before any write quiescence or cutover.

## Cutover state

Final cutover remains correctly blocked.

Required after the operator secret exists:
1. discover and verify the exact Shared Session Pooler host on port 5432;
2. run authenticated read-only target preflight;
3. quiesce source evidence writes;
4. take a fresh final source snapshot;
5. reconcile only an exact target prefix/delta;
6. finalize and verify sequence;
7. prove final exact identity;
8. switch runtime to the audited Supabase target;
9. redeploy and verify `database_target_mode=SUPABASE_POOLER`;
10. prove chain continuation, idempotency, restart recovery and prospective collection before closing the migration.

Old Render Postgres remains untouched as fallback.
