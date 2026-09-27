# UPBIT-KRW-LISTING-SHOCK-001 — WAYBACK NUMERIC DETAIL CENSUS TRANSPORT REMEDIATION V0.2.8A

Date: 2026-09-27
Status: FROZEN BEFORE EXECUTION / INDEX-ONLY / OUTCOME-BLIND

## Trigger

V0.2.8 returned HTTP 503 from the CDX endpoint for both numeric-detail wildcard queries. No archive payload was opened and no scientific coverage conclusion is accepted from that run.

## Purpose

Retry the exact same numeric-detail coverage question with lower-load CDX transport.

## Frozen transport remediation

For each family:
- LEGACY: api-manager.upbit.com/api/v1/notices/*
- MODERN: api-manager.upbit.com/api/v1/announcements/*

Query 2023 and 2024 separately.

For each family-year request:
- output=json
- filter=statuscode:200
- fields=timestamp,original,statuscode,mimetype,digest,length
- collapse=urlkey
- limit=10000
- max attempts=4
- retry only 408/425/429/500/502/503/504
- deterministic backoff 3, 6, 12 seconds

Accepted URL grammar and all V0.2.8 completeness gates remain unchanged.

No archived payload replay is authorized.

## Classification

If any family-year remains unavailable after the retry budget:
WAYBACK_NUMERIC_DETAIL_CENSUS_TECHNICAL_FAILURE

Otherwise evaluate the unchanged V0.2.8 completeness candidate gates:
- WAYBACK_NUMERIC_DETAIL_CENSUS_CANDIDATE
- WAYBACK_NUMERIC_DETAIL_COVERAGE_INSUFFICIENT

## Firewalls

No event payload/title/timestamp values.
No Binance/OHLCV/returns/PnL.
No source threshold or strategy changes.
No main merge.
