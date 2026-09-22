# CRYPTO EDGE RADAR — DEPLOY DRIFT MONITOR V0.1

Date: 2026-09-22
Status: OPERATIONAL OBSERVABILITY ONLY

Purpose:
Detect when the canonical Render service is running an older commit than the head of the canonical GitHub branch `crypto-edge-radar-postgres-v0.5`.

Read-only source:
`GET https://api.github.com/repos/joseluisvieira28-oss/Laboratorio/branches/crypto-edge-radar-postgres-v0.5`

Runtime identity:
`RENDER_GIT_COMMIT`

Classifications:
- IN_SYNC: deployed commit == canonical branch head
- STALE_RUNTIME: deployed commit != canonical branch head
- UNAVAILABLE_FAIL_CLOSED: public branch head cannot be verified
- NOT_RENDER_RUNTIME: no Render commit identity available

Cadence:
At most once per hour inside the Radar runtime. Existing cached result is reused between checks.

This monitor does NOT deploy anything automatically.

Firewalls:
science_changed=false
signal_changed=false
timing_changed=false
costs_changed=false
orders=false
exchange_mutation=false
live_capital=false
main_merge=false
