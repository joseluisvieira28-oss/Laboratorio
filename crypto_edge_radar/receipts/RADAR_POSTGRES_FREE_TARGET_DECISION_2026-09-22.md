# CRYPTO EDGE RADAR — FREE POSTGRES TARGET DECISION — 2026-09-22

Status: **TARGET_PROVISIONING_AUTH_REQUIRED**

## Current canonical store

- Render Postgres: `crypto-edge-radar-evidence-v04`
- Free plan
- Reported expiry: `2026-10-17T08:47:15.2559Z`
- Verified private backup exists as of 2026-09-22.
- Vendor-neutral restore tooling is validated and canonical.

## Provider reconnaissance

### Render Free Postgres — REJECTED AS DURABLE TARGET

Official Render documentation currently states:
- one active Free Postgres database per workspace;
- fixed 1 GB storage;
- Free Postgres expires 30 days after creation;
- Free Postgres has no managed backups.

This cannot provide a durable no-cost target and cannot be pre-provisioned beside the current Free database in the same workspace.

Official source:
https://render.com/docs/free

### Neon Free — PREFERRED TARGET FOR PROVISIONING PROBE

Current official Neon material states the Free plan includes standard Postgres projects with:
- 0.5 GB database storage per project;
- serverless scale-to-zero;
- free compute allowance;
- standard Postgres connection strings with SSL/TLS support.

The latest official Neon material available on 2026-09-22 describes 100 Free projects and 100 CU-hours/project/month; quotas can change and must be rechecked at provisioning time.

Official sources:
https://neon.com/blog/neon-backend-is-ga
https://neon.com/blog/how-to-make-the-most-of-neons-free-plan

Classification:
`PREFERRED_FREE_TARGET__PROVISIONING_CREDENTIAL_REQUIRED`

### Supabase Free — ACCEPTABLE FALLBACK

Current official Supabase pricing states:
- dedicated Postgres on Free;
- 500 MB database size/project;
- up to 2 active Free projects;
- Free projects may pause after one week of inactivity.

The Radar has regular writes while active, but inactivity semantics are an additional operational dependency relative to Neon.

Official source:
https://supabase.com/pricing

Classification:
`ACCEPTABLE_FREE_FALLBACK__PROVISIONING_CREDENTIAL_REQUIRED`

## Decision

Preferred provisioning order:
1. Neon Free
2. Supabase Free
3. Render paid upgrade only by separate spend authority
4. Re-creating rotating Render Free databases is emergency-only and is not the preferred durable design.

No target account, project, connection string or credential has been created or inferred in this execution.

## Existing migration readiness

Validated canonical artifacts:
- `authorities/RADAR_POSTGRES_PORTABILITY_V0.1.md`
- `radar/evidence_portability.py`
- `tools/restore_evidence_postgres.py`
- verified backup receipt `RADAR_EVIDENCE_BACKUP_CLOSEOUT_2026-09-22.json`

Target restore remains blocked until a legitimate target Postgres connection URL is available.

## Governance

No spend.
No source database mutation.
No cutover.
No science change.
No outcome change.
No trading/orders/wallets/exchange mutation/capital.
No merge to main.
