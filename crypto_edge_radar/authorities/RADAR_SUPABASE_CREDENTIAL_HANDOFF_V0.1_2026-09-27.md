# CRYPTO EDGE RADAR — SUPABASE CREDENTIAL HANDOFF V0.1 — 2026-09-27

Status: **OPERATOR SECRET INPUT REQUIRED / FINAL CUTOVER STILL NOT AUTHORIZED**

This handoff exists because connected tooling cannot safely assign or retrieve a database password for the dedicated Supabase role `radar_runtime`.

No secret may be pasted into GitHub, Google Drive, receipts, logs, or ChatGPT.

## Step A — assign a password privately inside Supabase

Open the existing project:
`crypto-edge-radar-evidence-v05`
(project ref `jqzdvgjeuveiktftyrlz`).

Use the Supabase Dashboard SQL Editor while signed in to the project.

Choose a new strong random password locally and run:

```sql
alter role radar_runtime with password '<YOUR-NEW-STRONG-PASSWORD>';
```

Do not share that password in chat.

The role is already least privilege:
- LOGIN;
- no superuser / createdb / createrole / replication / bypassrls;
- SELECT + INSERT only on the two Radar evidence tables;
- USAGE + SELECT only on the evidence id sequence;
- no UPDATE / DELETE / TRUNCATE / schema CREATE;
- role-specific RLS policies only.

## Step B — provide the secret directly to Render, not to ChatGPT

In the canonical Render service `crypto-edge-radar-v05-canary`, add/update:

`RADAR_SUPABASE_POOLER_PASSWORD=<the password from Step A>`

Do **not** set `RADAR_USE_SUPABASE_TARGET=true`.

Do not delete the existing source database URL.

At this stage the password is present only in Render as a secret environment variable.

## What happens next

After the password exists in Render, the existing audited read-only discovery probe can be enabled with the latest source/target identity.

The probe:
- tests bounded Supavisor Shared Session Pooler candidates on port 5432;
- uses username `radar_runtime.jqzdvgjeuveiktftyrlz`;
- requires SSL;
- starts a read-only transaction;
- reads only event count, key count, min/max id and chain head;
- logs no password and no full connection URL;
- accepts a host only if exactly one candidate matches the supplied audited target identity.

The exact pooler host must not be guessed or frozen before that probe succeeds.

## Current verified equality boundary

Point-in-time equality was verified at:
- events: 1098
- keys: 1020
- max id: 1098
- chain head: `2f673358393bfc3903077d57a83a4e575bbc4052bed1ab36d10c9b267b597425`
- key-binding SHA256: `fb42a5353c1fbb28cef971f538b66458548ba4d01c4069255ea4cb9656b483a9`
- sequence: 1098 / called=true

This boundary is observational only and will age as the source continues collecting. The discovery probe must therefore use a fresh identity at execution time.

## Explicitly forbidden before final cutover protocol

- do not set `RADAR_USE_SUPABASE_TARGET=true`;
- do not quiesce source merely to discover the host;
- do not delete the source URL;
- do not guess `aws-N-eu-central-1.pooler.supabase.com`;
- do not use the paid IPv4 add-on;
- do not expose the password in logs/chat/repo/Drive;
- do not change scientific rules or timing.

After successful host discovery, the separate frozen cutover protocol still requires:
1. source write quiescence;
2. final verified source snapshot;
3. exact-prefix target verification;
4. exact missing-suffix reconciliation if necessary;
5. sequence finalization if necessary;
6. final exact equivalence;
7. controlled target switch;
8. post-switch chain/backend verification;
9. prospective resume.

Safety:
science change=false
orders=false
exchange mutation=false
live capital=false
paid resource=false
main merge=false
