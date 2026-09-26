# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE AMENDMENT 006

**Date:** 2026-09-23  
**Status:** FROZEN BEFORE ANY CROSS-ASSET ECONOMIC OUTCOME IS OPENED  
**Scope:** reconcile official funding transport with pre-existing timestamp normalization  
**Authority:** additive; Amendments 001–005 remain historical and applicable where non-conflicting

## Trigger

Source Gate V0.1D proved:
- complete 43,824-hour market coverage for ETHUSDT, SOLUSDT and BNBUSDT;
- SOL daily gap completion adds exactly 120 missing hours;
- official funding transport returns the first event as `1609459200002`, i.e. **+2 ms** from the exact 2021-01-01 00:00 UTC hour.

This is the same timestamp representation already observed and frozen in Amendment 002.

No cross-asset economic outcome has been opened.

## Reconciled rule

For every official funding-history record:

1. preserve the raw `fundingTime`;
2. compute nearest exact UTC hour:
   `normalized = round(raw_fundingTime / 3,600,000) × 3,600,000`;
3. compute `abs(raw - normalized)`;
4. if deviation <= **1,000 ms**, use the normalized timestamp for:
   - position-held funding event timing;
   - exact markPriceKline fallback lookup;
   - deduplication and chronological event map;
5. if deviation > 1,000 ms, DATA_TIMESTAMP_BLOCKED / FAIL_CLOSED.

Pagination continues from the raw API `fundingTime + 1`, not the normalized time.

## Mark price

Unchanged:
- use official funding-record `markPrice` when present;
- if empty, use official Binance USD-M 1h `markPriceKline OPEN` at the **normalized** funding hour;
- unresolved mark => FAIL_CLOSED.

## Provenance

Evidence receipt must report:
- funding record count;
- maximum absolute funding timestamp deviation in ms;
- count of records with non-zero normalization;
- direct mark count;
- markPriceKline fallback count;
- unresolved mark count = 0.

## Unchanged science

No changes to universe, dates, 2026 lock, Parent/Sticky rules, costs, execution semantics, scientific gates or no-rescue rules.
