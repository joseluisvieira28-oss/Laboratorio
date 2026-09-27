# UPBIT-KRW-LISTING-SHOCK-001 — SOURCE RECOVERY AUTHORITY V0.2

Date: 2026-09-27
Branch: `upbit-krw-listing-shock-source-recovery-v0.2`

## Parent

Frozen MVE:
`UKLS-UPBIT-KRW-BINANCE-SPOT-001`

Parent source classification:
`SOURCE_ACCESS_BLOCKED_HTTP_403__REVERIFIED`

The economic experiment, source window, title parser, source minimums, Binance route, execution rules and protected periods remain unchanged.

## Purpose

Test whether an older first-party Upbit announcement-list path on the same official host can serve as a semantically equivalent transport/source surface without opening historical scientific outcomes.

Historical first-party path observed in prior public Upbit integrations:
`https://api-manager.upbit.com/api/v1/notices`

This authority does not assume equivalence. It authorizes only a current-page schema/transport probe before any 2023-2024 enumeration.

## Frozen probe endpoints

Exactly:

1. `https://api-manager.upbit.com/api/v1/notices?page=1&per_page=20&thread_name=general`
2. `https://api-manager.upbit.com/api/v1/notices?page=1&per_page=20&thread_name=press`
3. parent modern control:
   `https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=30&category=trade`

No additional endpoint or parameter may be added after this probe starts.

## Allowed transport

Ordinary unauthenticated browser-like HTTP only:
- standard User-Agent;
- Accept / Accept-Language;
- Referer / Origin where normal;
- normal cookies from an unauthenticated landing request if available.

No:
- proxy rotation;
- residential proxy;
- CAPTCHA bypass;
- anti-bot evasion;
- authentication;
- private API;
- session impersonation;
- scraping-evasion service.

## Probe evidence

For each endpoint record only:
- HTTP status;
- content type;
- response byte length;
- SHA-256;
- JSON top-level type;
- top-level keys;
- candidate row-array field name;
- row count;
- row field names from at most first three rows;
- presence/absence of fields semantically corresponding to:
  - id/uuid
  - title
  - listed_at/first_listed_at
  - category/thread name.

Do not emit titles, bodies, notice IDs, timestamps, or any event values.

## Classification

`LEGACY_OFFICIAL_SCHEMA_CANDIDATE_PASS` iff one legacy `/notices` probe:
- HTTP 200;
- returns a deterministic JSON notice array;
- exposes event identifier, title and listed timestamp fields sufficient for an equivalence audit.

Otherwise:
`LEGACY_OFFICIAL_ROUTE_NOT_USABLE`.

The modern control remains diagnostic only.

## Scientific firewall

This probe must not:
- traverse beyond page 1;
- serialize any event title/id/timestamp;
- enumerate 2023-2024;
- touch Binance archives;
- open any OHLCV;
- compute returns or PnL;
- access 2025/2026 Binance market data;
- change the frozen title parser;
- change source minimums;
- change the date window;
- change strategy parameters;
- merge to main.

If a legacy schema candidate passes, a separate authority must freeze the exact equivalence mapping and historical enumeration rules before any 2023-2024 source data is opened.
