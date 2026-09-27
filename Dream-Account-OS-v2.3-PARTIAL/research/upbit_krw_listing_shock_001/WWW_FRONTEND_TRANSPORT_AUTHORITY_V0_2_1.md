# UPBIT-KRW-LISTING-SHOCK-001 — WWW FRONTEND TRANSPORT AUTHORITY V0.2.1

Date: 2026-09-27
Status: FROZEN BEFORE EXECUTION / SOURCE-ONLY

## Trigger

V0.2 proved:
- legacy official /api/v1/notices routes now return HTTP 404;
- frozen modern api-manager announcement list remains HTTP 403 from GitHub-hosted runtime.

Current official Upbit Developer Center examples use the canonical notice URL under:
`https://www.upbit.com/service_center/notice?... `

A newly observed first-party hostname is:
`external-announcements.upbit.com`.

## Purpose

Determine whether the current official WWW frontend exposes a normal unauthenticated public transport path or references an official announcement data host that can be audited separately.

No historical announcement enumeration is authorized.

## Exact requests

1. GET `https://www.upbit.com/service_center/notice`
2. GET `https://external-announcements.upbit.com/`

Ordinary browser-like headers only.

No additional path guessing in this stage.

## Evidence allowed

For each response:
- HTTP status
- content type
- byte length
- SHA-256
- redirect target if any

For WWW HTML only:
- page title text length only, not value
- script/link hostnames
- exact first-party hostnames referenced
- boolean presence of strings:
  - api-manager.upbit.com
  - external-announcements.upbit.com
  - announcements
  - service_center/notice
- script src URLs may be retained only if they are first-party Upbit assets.

Do not serialize visible notice titles, IDs, timestamps or bodies.

## Classification

`WWW_FRONTEND_TRANSPORT_CANDIDATE` if the WWW notice page returns HTTP 200 HTML.

`EXTERNAL_ANNOUNCEMENT_HOST_CANDIDATE` if the external-announcements root returns a public non-authenticated response whose status/schema suggests a service endpoint.

Otherwise:
`NO_NEW_FIRST_PARTY_TRANSPORT_CANDIDATE`.

A candidate does not open history or outcomes. Any follow-up endpoint discovery requires a new prospective authority.

## Firewalls

No proxy rotation.
No auth.
No CAPTCHA bypass.
No anti-bot evasion.
No 2023-2024 enumeration.
No titles/IDs/timestamps.
No Binance.
No OHLCV/returns/PnL.
No strategy changes.
No main merge.
