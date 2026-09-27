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

Point-in-time equality was most recently verified at:
- observed source/target boundary: 2026-09-27 10:45 UTC
- events: 1099
- keys: 1021
- max id: 1099
- chain head: `c2111ee37f4b1312b3cec36f93d6f6e6235b9908bdbe568a84ecda5b71020fa3`
- key-binding SHA256: `997ed29199048fd5f3a4de9e3f4d7cdce2caf5326b08e6bd54ec412fde1f824f`
- sequence: 1099 / called=true

Source identity was produced by the canonical secret-safe `RADAR_EVIDENCE_IDENTITY_V0.1`; target identity was independently queried through the connected Supabase project. This remains a point-in-time observation, not final cutover authority.

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
