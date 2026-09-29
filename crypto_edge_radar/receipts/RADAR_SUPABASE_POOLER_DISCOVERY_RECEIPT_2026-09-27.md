# CRYPTO EDGE RADAR — SUPABASE SESSION POOLER DISCOVERY RECEIPT — 2026-09-27

Status: **EXACT SESSION POOLER DISCOVERED / FINAL CUTOVER NOT YET PERFORMED**

Authority:
`RADAR-SUPABASE-RUNTIME-ROLE-POOLER-DISCOVERY-V0.1`

## Operator secret verification

The operator confirmed the dedicated role password was assigned privately in Supabase and copied directly into the canonical Render service.

Independent Supabase metadata verification:
- role: `radar_runtime`
- password_set = true

The secret value was never read or exposed.

## Discovery deployment

Canonical service:
`crypto-edge-radar-v05-canary`

Deploy:
`dep-dashssjncjis73a7b770`

Deploy status:
`live`

Deployed commit:
`03f0858430fb9aa768410cecc5e8942c970fd4e3`

Database target mode remained:
`SOURCE`

## Fresh identity used for discovery

Source runtime identity observed before discovery:
- event_count = 1115
- key_count = 1037
- max_event_id = 1115
- chain_head_sha256 = `d3c5db1ff1e59d7f78b4f1957c85318b9ac20422904442f268c50de0e7c17fe1`
- key_binding_sha256 = `3554df494caa5140962cac9ca30b6dbacfd591c1bb0ba27f75ead6b915d9b75c`
- sequence_last_value = 1115
- sequence_is_called = true
- chain_verified = true

Supabase table counts at the discovery boundary:
- radar_events = 1115
- radar_event_keys = 1037

## Supavisor Session Pooler discovery

Probe mode:
- Shared Supavisor
- Session mode
- port 5432
- SSL required
- read-only transaction
- role `radar_runtime.jqzdvgjeuveiktftyrlz`
- indices tested: 0..9

Classification:
`EXACT_SESSION_POOLER_DISCOVERED`

Exactly one candidate matched the frozen identity:

`aws-0-eu-central-1.pooler.supabase.com:5432`

Accepted target observation:
- event_count = 1115
- key_count = 1037
- min_event_id = 1
- max_event_id = 1115
- chain_head_matches = true
- status = `EXACT_TARGET_MATCH`

All other candidates were rejected.

No database mutation was performed by discovery.
No password or complete connection string was emitted.

## Remaining operational boundary

The discovered hostname is non-secret, but the connected Render mutation tool refused to write `RADAR_SUPABASE_POOLER_HOST` after the secret was present.

No attempt was made to bypass that safety restriction.

Therefore final cutover remains blocked before write quiescence.

Required operator-side Render action:

Set in the canonical service:

`RADAR_SUPABASE_POOLER_HOST=aws-0-eu-central-1.pooler.supabase.com`

Do not change:
- `RADAR_SUPABASE_POOLER_PASSWORD`
- the existing source `RADAR_DATABASE_URL`

Do not yet enable:
`RADAR_USE_SUPABASE_TARGET=true`

After the host exists, the frozen authenticated target preflight must pass before source writes are quiesced.

## Safety

- science_changed = false
- outcomes_changed = false
- source_database_mutation = false
- target_database_mutation = false
- orders = false
- exchange_mutation = false
- live_capital = false
- paid_resource = false
- main_merge = false
- secret_value_exposed = false
- final_cutover_performed = false
