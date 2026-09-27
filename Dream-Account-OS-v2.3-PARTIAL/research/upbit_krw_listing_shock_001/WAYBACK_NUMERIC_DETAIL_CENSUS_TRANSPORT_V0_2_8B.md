# UPBIT-KRW-LISTING-SHOCK-001 — WAYBACK NUMERIC DETAIL CENSUS TRANSPORT V0.2.8B

Date: 2026-09-27
Status: FROZEN BEFORE EXECUTION / INDEX-ONLY / OUTCOME-BLIND

Use the already-proven low-load CDX wildcard transport from V0.2.2:

- api-manager.upbit.com/api/v1/notices*
- api-manager.upbit.com/api/v1/announcements*

Query 2023-2024, statuscode:200, output=json, fields timestamp,original,statuscode,mimetype,digest,length, limit=5000, with no collapse.

Filter locally to exact numeric detail paths:
- ^/api/v1/notices/[0-9]+$
- ^/api/v1/announcements/[0-9]+$

The scientific question and completeness gates are unchanged from V0.2.8:
- >=100 distinct numeric IDs
- numeric coverage fraction exactly 1.0
- zero missing IDs in min..max
- max internal gap <=1
- earliest capture <= 2023-01-07T23:59:59Z
- latest capture >= 2024-12-25T00:00:00Z
- no transport/index parse failure.

No archived payload replay, event values, Binance, OHLCV, returns or PnL.
