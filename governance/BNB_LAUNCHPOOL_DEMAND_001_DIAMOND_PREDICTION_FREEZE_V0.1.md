# BNB-LAUNCHPOOL-DEMAND-001 — DIAMOND PREDICTION FREEZE V0.1

**Freeze ID:** `BNB-LAUNCHPOOL-DIAMOND-V0.1-2026-09-24`  
**Parent candidate:** `BNB-LAUNCHPOOL-DEMAND-001`  
**Governing policies:** `ND-PROMOTION-POLICY-V3.0-FROZEN`, `DIAMOND-TEST-V1-FROZEN-2026-09-24`  
**Status:** `FROZEN_MEASUREMENT_SPEC / SHADOW_ONLY / NO_TRADING_AUTHORITY`

## 1. Scientific identity — unchanged

This freeze does **not** alter the parent trading hypothesis.

Preserved parent rule:
- qualifying event: official Binance Launchpool announcement with explicit BNB utility under the already-frozen authority;
- direction: LONG BNBBTC;
- entry: first 15-minute open strictly after canonical announcement timestamp;
- hold: 24h;
- base cost: 20 bps;
- stress cost: 30 bps;
- one active trade;
- <=60-minute information clustering;
- no stop;
- no target;
- no leverage.

If any parent field conflicts with the canonical parent authority, the canonical parent authority wins and this Diamond freeze becomes `BLOCKED_AUTHORITY_MISMATCH` before outcomes are used.

## 2. Extraordinary prediction

Before the next genuinely prospective eligible event is resolved, freeze the following statement:

> A qualifying Launchpool event that creates explicit BNB utility should produce a BNB-specific demand shock visible first in the event-time market response and should leave a positive 24h BNBBTC return after the already-frozen base cost more often and with greater magnitude than would be consistent with an isolated historical tail.

The parent 24h economic result remains the primary endpoint. The new measurements below are **mechanism diagnostics only** and cannot change the trade rule.

## 3. Prospective causal fingerprint — measurement only

For every next eligible event, record immutably:

1. canonical announcement timestamp and source receipt;
2. exact parent entry timestamp;
3. BNBBTC returns over:
   - T0 -> +15m,
   - T0 -> +60m,
   - parent entry -> +24h;
4. BNBUSDT and BTCUSDT returns over the same short event windows for attribution context;
5. BNB spot volume over T0 -> +60m compared with a trailing, pre-event baseline computed using one fixed implementation frozen before the event;
6. source completeness / stale-data / duplicate-event status;
7. frozen base and stress net 24h parent economics;
8. whether the event overlaps another already-active parent event.

The volume-baseline implementation must be frozen in code before the next event. It may not be calibrated against historical Launchpool outcomes.

## 4. Interpretation rules

The causal fingerprint is supportive when the BNB-specific short-window response is directionally consistent with discrete BNB demand.

It is contradictory when repeated clean prospective events show:
- no BNB-specific short-window response, or
- a response systematically opposite to the demand-shock mechanism,
while source and execution integrity are valid.

No single event can establish `DIAMOND_TEST_SURVIVES`.

## 5. Parent economic adjudication

The exact minimum prospective sample for a final Diamond verdict must be frozen **before** the first event counted by this Diamond freeze.

Because the mechanism is rare/event-driven, sample adequacy must be mechanism-aware and must not be invented after outcomes.

Until that minimum is frozen and reached, state is:
`DIAMOND_TEST_COLLECTING / NO_FINAL_VERDICT`.

## 6. Hard anti-rescue constraints

After the first counted event:
- no change to event definition;
- no change to direction;
- no change to entry or 24h horizon;
- no change to costs;
- no event deletion;
- no filtering by event "quality";
- no change to clustering;
- no alternative pair substitution;
- no volume threshold selected from observed event outcomes;
- no post-outcome minimum-sample reduction;
- no live-order interpretation from this document.

## 7. Operational next step

Implement only a **public/read-only, measurement-only receipt path** for the causal fields above and bind it to the existing BNB watcher without changing its scientific rule.

Before first eligible event:
- freeze the volume-baseline code and hash;
- freeze the prospective sample minimum;
- prove duplicate/stale/source guards;
- emit an immutable pre-event receipt.

No authenticated exchange API, order, wallet, capital, leverage, webhook execution, or exchange mutation is authorized.
