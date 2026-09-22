# CRYPTO EDGE RADAR — PERSISTENCE EXPIRY MONITOR V0.1

Date: 2026-09-22
Status: OPERATIONAL OBSERVABILITY ONLY

Purpose:
Expose the known canonical Postgres expiry risk directly in the Radar runtime state without changing any scientific or execution behavior.

Configuration:
- RADAR_PERSISTENCE_EXPIRY_UTC
- current canonical value: 2026-10-17T08:47:15.2559Z

Classification:
- UNKNOWN: no configured expiry
- OK: > 14 days remaining
- WARN: > 7 and <= 14 days remaining
- CRITICAL: <= 7 days remaining
- EXPIRED: now >= expiry

This monitor MUST NOT:
- alter global scientific health solely because a future expiry is approaching;
- change signal timing, rules, costs, thresholds or sources;
- create orders or capital authority;
- mutate the evidence store.

It may expose:
- expiry timestamp
- days/hours remaining
- classification
- backup status reference
- migration readiness reference

Firewalls:
science_changed=false
signal_changed=false
timing_changed=false
database_mutation=false
live_trading=false
orders=false
exchange_mutation=false
capital=false
main_merge=false
