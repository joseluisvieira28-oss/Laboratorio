# CRYPTO EDGE RADAR — PRIVATE EVIDENCE BACKUP V0.1

Date: 2026-09-22
Status: TEMPORARY READ-ONLY BACKUP AUTHORITY

## Risk

The canonical Render Postgres evidence store is on the free plan and reports expiry at:
2026-10-17T08:47:15.2559Z.

The evidence chain must be backed up and independently verified before expiry.

## Authorized temporary mechanism

Expose a temporary GET endpoint only when:
- RADAR_BACKUP_EXPORT_ENABLED=true
- query token exactly matches RADAR_BACKUP_EXPORT_TOKEN

The endpoint may read:
- radar_events
- radar_event_keys

It must use a read-only database transaction where supported.

The response may contain:
- complete append-only event rows
- complete idempotency key rows
- chain verification result
- chain head SHA256
- deterministic snapshot SHA256

It must never contain:
- database URL
- database password
- Render credentials
- exchange credentials
- environment variable values
- trading secrets

Wrong/missing token returns 404.

## Lifecycle

1. Freeze this authority before deployment.
2. Generate a one-time high-entropy token outside repository content.
3. Set token only as Render environment variable.
4. Download one snapshot.
5. Independently verify the full hash chain.
6. Store a private backup artifact.
7. Remove the endpoint and token.
8. Redeploy clean runtime.

## Firewalls

database_mutation=false
science_changed=false
signals_changed=false
outcomes_changed=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
capital=false
main_merge=false
public_unauthenticated_export=false
