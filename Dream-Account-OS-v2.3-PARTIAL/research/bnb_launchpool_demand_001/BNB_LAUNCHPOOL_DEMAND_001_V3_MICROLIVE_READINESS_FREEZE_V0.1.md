# BNB-LAUNCHPOOL-DEMAND-001 — V3 MICRO-LIVE RESEARCH READINESS FREEZE V0.1

**Date:** 2026-09-17  
**Governing policy:** `ND-PROMOTION-POLICY-V3.0-FROZEN`  
**Parent V3 closeout:** `BNB_LAUNCHPOOL_DEMAND_001_V3_READJUDICATION_CLOSEOUT_2026-09-17.md`  
**Status:** `FROZEN_READINESS_SPEC__NOT_EXECUTION_AUTHORIZATION`

## Purpose

Prepare the smallest scientifically legitimate path from V3 Tier 2 to micro-live research without waiting for an arbitrary 25-event forward sample.

This file does not authorize an order. It freezes the conditions that must be satisfied before a separate explicit execution authorization may permit one micro-live research observation.

## Immutable signal

No signal modification is permitted:
- canonical official Binance Launchpool publication strictly after the existing forward-shadow boundary;
- publication must explicitly create BNB staking/locking/farming utility under the existing source authority;
- LONG BNBBTC spot;
- entry at first 15m open strictly after canonical announcement timestamp;
- 24h hold;
- BASE 20 bps / STRESS 30 bps research accounting;
- one active trade maximum;
- <=60-minute information clustering;
- no stop, target, leverage, regime filter, token filter or manual event deletion.

## Pre-execution gates

Every gate is fail-closed:
1. Candidate remains V3 Tier 2 with no later canonical contradiction.
2. Event is genuinely prospective relative to the existing forward-shadow boundary and this readiness freeze.
3. Canonical official-source timestamp and eligibility parse pass unchanged source rules.
4. BNBBTC market exists and is observable through an approved read-only market-data route.
5. Entry price can be timestamp-bound to the exact first eligible 15m open without lookahead.
6. No unresolved source/data gap, timestamp ambiguity, duplicate event, overlapping active trade or clustering violation.
7. No exchange API key, wallet, authenticated trading connector or order path may be activated by this readiness file.
8. A separate explicit `BNB-LAUNCHPOOL-DEMAND-001 V3 MICRO-LIVE EXECUTION AUTHORITY` must exist before any order.

## Frozen micro-live research envelope for a future execution authority

If and only if a separate explicit execution authority is later created and authorized:
- maximum real-money notional per event: **CHF 25 equivalent**;
- if venue minimum executable notional exceeds CHF 25 equivalent: **NO TRADE**;
- leverage: **0 / forbidden**;
- maximum simultaneous positions from this candidate: **1**;
- no averaging down, pyramiding, martingale, discretionary add, stop change or early profit-taking;
- exit: exact frozen 24h rule;
- manual override may only cancel/abort for safety or execution failure and must be logged; it cannot improve the backtest rule;
- any material source mismatch, venue outage, pair change, abnormal spread/liquidity condition preventing frozen execution, or reconciliation failure => **NO TRADE / KILL**;
- full order/fill/fee/slippage/timestamp reconciliation required before the event can count as micro-live evidence.

## Evidence role

One micro-live event is operational evidence only. It cannot by itself create Tier 1, change the historical effect estimate, justify scaling, or tune the signal.

Tier 1 requires a separately frozen adjudication contract specifying the prospective evidence needed for validation.

## Forbidden

- no automatic live activation;
- no order from this file;
- no exchange mutation;
- no wallet operation;
- no leverage;
- no alert/webhook that can place orders;
- no 2026 backfill used as a new historical rescue;
- no deletion of losing forward events;
- no event/horizon/pair/cost/direction change;
- no merge to main without separate authorization.

## Current state

`READINESS_SPEC_FROZEN__AWAIT_SEPARATE_EXECUTION_AUTHORITY_AND_GENUINELY_PROSPECTIVE_EVENT`
