# CRYPTO EDGE RADAR — SUPABASE TARGET EQUIVALENCE RECEIPT V0.1 — 2026-09-27

Status: **PRE-CUTOVER TARGET EQUIVALENCE VERIFIED / CONNECTION CREDENTIAL BLOCKED**

## Source backup boundary

Verified source snapshot:
- events: 1032
- event keys: 954
- event ids: 1..1032
- chain head: `f8b85ba3d45dcb426e37d1a1da543cff61a85d9ea0a01ddc1a07662b9e7c02cd`
- canonical snapshot SHA256: `6c74bdcf1013b1ab49fdcefd2e046db6471ea2816c6b425f4a6378dda22de9cb`
- Drive backup file: `1oam9hmileBQbV80C6o0cQUicXfu-vzvZ`
- source receipt: `RADAR_EVIDENCE_BACKUP_CLOSEOUT_2026-09-27.json`

## Target

Provider: Supabase
Project name: `crypto-edge-radar-evidence-v05`
Project ref: `jqzdvgjeuveiktftyrlz`
Organization plan: Free
Region: `eu-central-1`
Project status observed: `ACTIVE_HEALTHY`
Postgres engine: 17

The target already existed before this verification. No new project and no paid resource were created by this attack.

## Exact target verification

Server-side target verification:
- event_count = 1032
- min event id = 1
- max event id = 1032
- distinct event ids = 1032
- payload SHA256 mismatches = 0
- previous-chain mismatches = 0
- chain SHA256 mismatches = 0
- target chain head = source chain head
- key_count = 954
- orphan event keys = 0
- BIGSERIAL sequence last_value = 1032

Independent deterministic rowset digests computed from the source backup and separately inside target Postgres:

- event rowset SHA256:
  `f1fdde4843b8c33f42a2a90896ef4d86df411d02c00e25d551576b53f7a8efa2`
- event-key rowset SHA256:
  `978f6eea3070fbadd73ccb4688028a9f3dcf07ab5876ccdc47cfa53c2debf02d`

Both target digests exactly equal the independently computed source-backup digests.

Classification:
`TARGET_EXACT_AT_BACKUP_BOUNDARY`

This does not claim that target remains synchronized after the backup boundary. A final quiesced source snapshot and final exact restore/reconciliation are still required before cutover.

## Target exposure/security

Only two public tables were observed:
- `public.radar_events`
- `public.radar_event_keys`

Both have RLS enabled and no RLS policies.
Observed table grants are limited to `postgres` and `service_role`; no `anon` or `authenticated` table grants were observed.
Supabase security advisor reports only informational `rls_enabled_no_policy` findings for the two tables, consistent with deny-by-default Data API access.
Supabase performance advisor reported no findings.

No RLS/policy/grant mutation was performed.

## Remaining cutover blocker

The canonical Render runtime currently reports:
`target_url_configured=false`

The available connected Supabase tooling does not expose/reset the database password or a complete Postgres connection credential. Therefore no connection URL was invented, inferred or printed.

Remaining operator input required before actual cutover:
- supply a legitimate Supabase Postgres session/direct connection URL as a secret to the controlled cutover process / Render runtime.

After that credential exists, the frozen cutover protocol still requires:
1. write quiescence;
2. final source snapshot;
3. independent final verification;
4. exact target reconciliation/restore;
5. target verification;
6. DATABASE_URL switch;
7. redeploy and chain verification;
8. prospective resume.

## Governance

- source database mutation: false
- target mutation during this verification: false
- new project creation: false
- spend: false
- science changed: false
- outcomes changed: false
- orders: false
- exchange mutation: false
- live capital: false
- main merge: false
