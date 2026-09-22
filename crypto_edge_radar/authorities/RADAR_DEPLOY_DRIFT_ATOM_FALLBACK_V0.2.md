# CRYPTO EDGE RADAR — DEPLOY DRIFT ATOM FALLBACK V0.2

Date: 2026-09-22
Status: OPERATIONAL OBSERVABILITY ONLY / FROZEN BEFORE IMPLEMENTATION

## Problem

The V0.1 deploy-drift monitor correctly compared `RENDER_GIT_COMMIT` with the
canonical GitHub branch head, but the unauthenticated GitHub REST branch endpoint
can return HTTP 403 rate-limit responses from Render. That produces
`UNAVAILABLE_FAIL_CLOSED` even when the runtime may be healthy.

## Frozen fallback

Primary source remains the public GitHub REST branch endpoint.

Only if the REST source fails or does not provide an exact 40-hex SHA, V0.2 may
read the public Atom feed for the same canonical branch:

`https://github.com/joseluisvieira28-oss/Laboratorio/commits/crypto-edge-radar-postgres-v0.5.atom`

The fallback accepts a head only when the FIRST feed entry exposes exactly one
canonical GitHub commit URL containing a 40-character hexadecimal commit SHA.

No short SHA, timestamp inference, title matching, HTML scraping, nearest commit,
or branch activity proxy is admissible.

## Classification

- IN_SYNC: deployed SHA == exact canonical head SHA
- STALE_RUNTIME: deployed SHA != exact canonical head SHA
- UNAVAILABLE_FAIL_CLOSED: neither exact source can prove a head
- NOT_RENDER_RUNTIME: no deployed Render SHA available

The receipt records `head_source` as `GITHUB_REST` or `GITHUB_ATOM`.

## Firewalls

automatic_deploy=false
science_changed=false
signal_changed=false
timing_changed=false
costs_changed=false
orders=false
exchange_mutation=false
live_capital=false
main_merge=false
