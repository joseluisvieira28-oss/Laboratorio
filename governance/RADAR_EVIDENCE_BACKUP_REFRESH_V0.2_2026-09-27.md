# CRYPTO EDGE RADAR — EVIDENCE BACKUP REFRESH V0.2 — 2026-09-27

Status: FROZEN READ-ONLY BACKUP REFRESH

Authority ID: `RADAR-EVIDENCE-BACKUP-REFRESH-V0.2-2026-09-27`

## Purpose

Create a fresh, independently verified, read-only backup of the canonical Postgres evidence store before the current Render Free Postgres expiry.

Source database:
- Render id: `dpg-dalqi4qd0e5s738a77kg-a`
- name: `crypto-edge-radar-evidence-v04`
- region: Frankfurt
- plan: Free
- expiry: `2026-10-17T08:47:15.2559Z`
- external IP allowlist: empty

## Required method

1. Use only the existing GitHub Actions secret `RADAR_DATABASE_URL`.
2. Never print or persist the secret.
3. Export through `tools/export_evidence_snapshot_readonly.py`.
4. Source transaction must remain read-only.
5. Verify the exported snapshot independently after export:
   - payload_sha256 for every event;
   - prev_chain_sha256 continuity;
   - chain_sha256 recomputation;
   - event ids strictly increasing;
   - every event_key references an existing event_id;
   - event/key counts match the snapshot receipt;
   - recomputed snapshot SHA matches the snapshot metadata.
6. Package the snapshot as a ZIP artifact.
7. Copy the exact artifact bytes to Google Drive for durability outside Render/GitHub Actions retention.
8. Record artifact digest, snapshot digest, event count, key count, chain head, workflow run id and Drive file id in the closeout.

## Firewalls

- no INSERT/UPDATE/DELETE/TRUNCATE/DDL;
- no source schema changes;
- no target database creation;
- no paid resources;
- no DATABASE_URL exposure;
- no trading;
- no orders;
- no exchange mutation;
- no capital;
- no scientific rule/threshold/cost/timing changes;
- no promotion/demotion decisions;
- no main merge.

This branch/PR exists solely to trigger and audit the backup refresh and may be closed after the verified artifact is preserved externally.
