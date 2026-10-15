# LIDO-WITHDRAWAL-QUEUE-PRESSURE-001 — SOURCE COLLECTION PROTOCOL V0.1

Date: 2026-09-27  
Status: FROZEN_SOURCE_ONLY / PROSPECTIVE / NO MARKET OUTCOMES  
Primary authority: official Lido Withdrawals API

## Purpose

Preserve fresh, point-in-time queue-state source observations for a future scientific hypothesis without opening any crypto market response.

This protocol is deliberately predictor-only.

## Canonical endpoint

https://wq-api.lido.fi/v2/request-time/calculate

The source gate has already demonstrated:
- HTTP 200;
- non-empty JSON;
- top-level fields including status, requestInfo and nextCalculationAt;
- canonical WithdrawalQueueERC721 bytecode present independently.

## Observation contract

Each collection run must preserve:
1. fetch timestamp UTC;
2. HTTP status;
3. exact raw JSON payload;
4. SHA256 of raw response bytes;
5. source URL;
6. parsed top-level schema only for diagnostics;
7. no external crypto price, return, funding, basis, volume or PnL data.

No queue threshold is defined.
No LONG/SHORT direction is defined.
No response asset is defined.
No holding period is defined.
No economic outcome is defined.

## Contamination boundary

The prior STETH-REDEMPTION-BASIS-002 2023-2024 market-response corpus gives this new ID zero promotion credit.

Fresh source observations collected under this protocol may later be used to design/calibrate a predictor-state definition, but any economic response test must:
- receive a separate new pre-outcome freeze;
- start after that freeze;
- use fresh, untouched response outcomes;
- disclose any predictor observations seen during calibration.

## Fail-closed rules

- non-200 HTTP -> SOURCE_COLLECTION_FAIL
- invalid/non-JSON payload -> SOURCE_COLLECTION_FAIL
- missing status/requestInfo/nextCalculationAt -> SOURCE_SCHEMA_FAIL
- source URL change -> new authority required
- any market-price/outcome fetch -> protocol violation

## Authorization boundary

Authorized:
- public read-only Lido queue API fetch;
- hashing;
- artifact persistence;
- schema inspection.

Not authorized:
- market-response computation;
- trading signal;
- PnL;
- 2023-2024 retrospective rescue;
- live trading;
- orders;
- exchange mutation;
- capital;
- main merge.
