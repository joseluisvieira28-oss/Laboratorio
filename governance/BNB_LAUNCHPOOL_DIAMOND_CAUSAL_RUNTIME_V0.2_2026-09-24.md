# BNB-LAUNCHPOOL-DEMAND-001 — DIAMOND CAUSAL RUNTIME V0.2 — 2026-09-24

**Status:** CODE READY / NOT ARMED / PROSPECTIVE ONLY  
**Parent:** `BNB-LAUNCHPOOL-DEMAND-001`  
**Measurement authority:** `BNB-LAUNCHPOOL-DIAMOND-V0.2-2026-09-24` from draft PR #88  
**Activation:** OFF by default via `BNB_DIAMOND_V02_ENABLED=false`

## Purpose

Implement the already-frozen Diamond V0.2 causal fingerprint before any genuinely prospective eligible Launchpool event has appeared in the canonical runtime.

The implementation is additive. It does not change the parent Launchpool event definition, cluster rule, BNBBTC trade direction, 15m entry, 24h hold, costs, overlap rule, or parent resolution.

## Causal measurement

For each parent-selected, non-overlap eligible event:

- align to the first complete 1-minute bar strictly after the canonical announcement timestamp;
- use public/read-only Binance Spot 1m data;
- measure BNBBTC return at 15m and 60m;
- measure BNBUSDT and BTCUSDT returns at 15m and 60m as attribution context;
- measure BNBUSDT quote volume over 60m;
- compare that volume with the median of the most recent 20 prior UTC dates with a complete same-clock 60m window;
- scan at most 40 calendar days to obtain those 20 valid baseline days;
- never calibrate the baseline against Launchpool outcomes.

If the 60m event window has not completed, state is `WAITING_CAUSAL_WINDOW`.

If fewer than 20 valid baseline dates exist inside the frozen 40-day lookback, the event is recorded as `MECHANISM_DATA_BLOCKED` and cannot silently count toward Diamond evidence.

Transient source/transport failures are not converted into scientific negatives and remain retryable.

## First-25 adjudication

Final V0.2 Diamond evidence uses the first 25 chronologically matched events that have both:

1. complete causal measurement; and
2. parent `BNB_FORWARD_RESOLUTION`.

At 25, all are required:

- BASE20 mean > 0;
- BASE20 PF > 1;
- largest single positive BASE-net trade share <= 40%;
- >=17/25 events with positive BNBBTC 60m return;
- median BNBBTC 60m return > 0;
- >=17/25 events with BNBUSDT volume-shock ratio > 1;
- median volume-shock ratio > 1;
- missed eligible prospective observations = 0.

Before 25, classification is always `DIAMOND_TEST_COLLECTING`, regardless of how good or bad the partial PnL looks.

At 25:
- all gates pass -> `DIAMOND_TEST_SURVIVES__REVIEW_REQUIRED`;
- any scientific gate fails -> `DIAMOND_TEST_FAIL__EXACT_CANDIDATE_NO_RESCUE`.

No automatic Tier promotion follows either state.

## Runtime isolation

The feature is not activated merely by code presence.

`BNB_DIAMOND_V02_ENABLED` must be explicitly set true in a separately authorized deployment before the minute-data measurement route is constructed.

When disabled:
- parent BNB watcher behavior is unchanged;
- no new 1m Diamond source calls occur;
- Diamond metrics may read already-persisted evidence only;
- Diamond Board reports code-ready/not-armed.

## Governance

- public/read-only source only;
- no authenticated exchange API;
- no API key;
- no order;
- no exchange mutation;
- no wallet;
- no leverage;
- no capital;
- no strategy-rule change;
- no cost reduction;
- no event deletion;
- no early verdict;
- no main merge implied;
- no Render activation implied.
