# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE AMENDMENT 005

**Date:** 2026-09-23  
**Status:** FROZEN BEFORE ANY CROSS-ASSET ECONOMIC OUTCOME IS OPENED  
**Scope:** official funding timestamp normalization only  
**Authority:** supersedes prior timestamp-handling clauses where they conflict; preserves Amendment 004 mark-price hierarchy

## Trigger

Source Gate V0.1C failed before any economic outcome was opened because official Binance funding-history records included timestamps such as:

`1609459200002`

for the funding event corresponding to:

`2021-01-01 00:00:00 UTC = 1609459200000`

Observed deviation:
**+2 milliseconds**.

Price coverage remained complete.

## Frozen normalization rule

For each official funding-history `fundingTime`:

1. preserve `raw_funding_time_ms`;
2. compute:
   `normalized_funding_time_ms = round(raw / 3,600,000) × 3,600,000`;
3. compute absolute deviation in milliseconds;
4. normalize only when deviation <= **1,000 ms**;
5. if deviation > 1,000 ms:
   **DATA_TIMESTAMP_BLOCKED / FAIL_CLOSED**.

No rate, markPrice, asset, period, signal, threshold, fee, slippage or execution rule changes.

## Duplicate handling

After normalization:
- if two records map to the same normalized timestamp and their fundingRate + resolved markPrice agree within numerical precision, deduplicate;
- if they conflict, **FAIL_CLOSED**.

## Mark-price hierarchy preserved

Amendment 004 remains authoritative:
1. use funding-history record `markPrice` when present and valid;
2. only if empty, use official Binance USD-M 1h `markPriceKline OPEN` at the normalized funding timestamp;
3. if no exact fallback exists, DATA_BLOCKED.

## Funding cashflow

For a long open across the normalized funding event:

`funding_cashflow = -qty × resolved_markPrice × fundingRate`

The fundingRate and markPrice remain those of the official record/frozen fallback. Only the timestamp used to align the event to the 1h causal engine is normalized.

## Audit requirements

Evidence must record:
- raw timestamp;
- normalized timestamp;
- deviation_ms;
- maximum observed deviation;
- number of normalized records;
- number of exact-hour records;
- any duplicate deduplications;
- zero deviations > 1,000 ms.

## Outcome boundary

All economic workflow attempts before a PASS under Amendment 005 remain:

**INVALID_UNOPENED_DO_NOT_USE**

A fresh Source Gate must PASS before the adjudicating economic trigger is fired.
