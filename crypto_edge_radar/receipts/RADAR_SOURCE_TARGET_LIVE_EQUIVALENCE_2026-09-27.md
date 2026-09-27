# CRYPTO EDGE RADAR — SOURCE ↔ TARGET LIVE EQUIVALENCE V0.1 — 2026-09-27

Status: **POINT-IN-TIME LIVE EQUIVALENCE VERIFIED / CUTOVER NOT AUTHORIZED**

Authority context:
- `RADAR_POSTGRES_CUTOVER_PROTOCOL_V0.1.md`
- `RADAR_POSTGRES_CUTOVER_PRESEEDED_TARGET_AMENDMENT_V0.2.md`
- `RADAR-POSTGRES-APPEND-ONLY-PREFIX-RECONCILIATION-V0.1`
- `RADAR-SUPABASE-RUNTIME-ROLE-POOLER-DISCOVERY-V0.1`

## Source

Canonical Render service:
- service: `crypto-edge-radar-v05-canary`
- canonical branch: `crypto-edge-radar-postgres-v0.5`
- deployed commit: `26298533da12ad99b92100c687cafd7094d9873e`
- runtime health: `OK`
- evidence backend: `postgres`
- evidence identity schema: `RADAR_EVIDENCE_IDENTITY_V0.1`
- checked heartbeat: `2026-09-27T10:30:43.01046883Z`

Secret-safe source identity:
- event_count: **1098**
- max_event_id: **1098**
- key_count: **1020**
- chain_head_sha256: `2f673358393bfc3903077d57a83a4e575bbc4052bed1ab36d10c9b267b597425`
- key_binding_sha256: `fb42a5353c1fbb28cef971f538b66458548ba4d01c4069255ea4cb9656b483a9`
- sequence_last_value: **1098**
- sequence_is_called: **true**
- chain_verified: **true**
- payloads_exposed: **false**
- database_mutation: **false**

## Target

Supabase project:
- ref: `jqzdvgjeuveiktftyrlz`
- name: `crypto-edge-radar-evidence-v05`
- region: `eu-central-1`
- plan: Free
- status previously observed: `ACTIVE_HEALTHY`

Read-only target verification at the same operational checkpoint:
- event_count: **1098**
- min_event_id: **1**
- max_event_id: **1098**
- key_count: **1020**
- chain_head_sha256: `2f673358393bfc3903077d57a83a4e575bbc4052bed1ab36d10c9b267b597425`
- key_binding_sha256: `fb42a5353c1fbb28cef971f538b66458548ba4d01c4069255ea4cb9656b483a9`
- sequence_last_value: **1098**
- sequence_is_called: **true**

No target row mutation was performed by this verification.

## Equality checks

PASS:
- source event count == target event count;
- source max event id == target max event id;
- target ids begin at 1 and end at source max id;
- source key count == target key count;
- source chain head == target chain head;
- source deterministic key-binding digest == target deterministic key-binding digest;
- source sequence last value == target sequence last value;
- source and target sequence are both called.

Classification:
**LIVE_METADATA_AND_CHAIN_EQUIVALENCE_VERIFIED_AT_1098**

This is materially stronger than count-only parity because it binds:
1. append-chain identity through the final event hash;
2. the complete event-key binding set through a deterministic SHA-256 digest;
3. sequence continuity.

It still does not replace the frozen final quiesced snapshot requirement.

## Remaining blockers / mandatory final steps

The final database switch remains forbidden until all frozen cutover steps pass:

1. obtain a legitimate secret password for dedicated role `radar_runtime`;
2. obtain/discover the exact Supavisor Shared Session Pooler host; do not infer the cluster index;
3. validate the read-only pooler probe with the audited target identity;
4. enter `RADAR_EVIDENCE_WRITES_QUIESCED=true`;
5. take a final source snapshot;
6. independently verify that final source snapshot;
7. verify target is an exact prefix of that final source;
8. reconcile only any missing exact suffix;
9. finalize and verify sequence if a suffix was inserted;
10. prove final exact target equivalence;
11. only then set the controlled target runtime switch and redeploy;
12. verify backend, evidence chain and prospective recovery before resuming normal collection.

The currently available connected Supabase tooling exposes no supported database-password reset/set action. Prior SQL password assignment attempts were blocked by the tool safety layer. No credential has been invented, inferred, committed, logged, written to Drive, or printed.

## Safety

- scientific rule change: false
- outcome change: false
- source evidence mutation by this verification: false
- target evidence mutation by this verification: false
- authenticated exchange API: false
- orders: false
- exchange mutation: false
- live capital: false
- paid resource: false
- main merge: false
- cutover authorized: false
