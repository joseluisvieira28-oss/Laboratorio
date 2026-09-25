# OPTIONS-SPOTPERP-001-V2.1 — PUBLIC EXECUTION SHADOW V0.1 — 2026-09-25

**Status:** FROZEN PROSPECTIVELY BEFORE FIRST ELIGIBLE EXECUTION OBSERVATION  
**Authority ID:** `OPTIONS-SPOTPERP-001-V2.1-PUBLIC-EXECUTION-SHADOW-V0.1`  
**Parent authority:** `OPTIONS-SPOTPERP-001-V2.1-FORWARD-EVIDENCE-GATE-V0.1`

## Purpose

Accumulate prospective, read-only operational evidence for the exact frozen OPTIONS-SPOTPERP-001-V2.1 candidate in parallel with the already-running first-50 statistical forward block.

This authority does not alter the parent signal, position sign, risk scaling, BTC return definition, horizon, BASE10 cost, STRESS20 cost, first-50 window, or Tier-1 statistical thresholds.

## Prospective boundary

- first eligible parent entry date: **2026-09-26 UTC**
- parent entry dates before 2026-09-26 are excluded from this execution-shadow sample and are not reconstructed;
- only already-persisted parent `OPTIONS_V21_FORWARD_ENTRY` records may trigger an observation;
- an observation is attempted only on the same UTC date as the parent entry;
- a parent entry discovered only after its UTC entry date is recorded as a missed operational observation, not backfilled;
- transient public-source failure is retryable during the same day and is not converted into scientific PnL.

The Git commit containing this authority is the freeze evidence. Implementation must be additive and subsequent.

## Frozen implementation mapping

Parent scientific execution remains:
- BTCUSDT 00:00 UTC t+1 to 00:00 UTC t+2;
- position > 0 = LONG;
- position < 0 = SHORT;
- risk scaling unchanged;
- BASE10 / STRESS20 unchanged.

Public implementation-shadow routes:

### LONG
- venue: MEXC Spot;
- symbol: BTCUSDT;
- public GET-only market data;
- observe best bid/ask, spread, public depth and current public symbol support;
- general public spot taker fee reference: 5 bps one-way / 10 bps round trip;
- no funding for unlevered spot.

### SHORT
- venue: MEXC USDT Perpetual;
- symbol: BTC_USDT;
- public GET-only market data;
- observe best bid/ask, spread, contract metadata, public depth, current funding and clock diagnostics;
- public futures taker fee reference: 8 bps one-way / 16 bps round trip;
- current-rate 24h funding calculation is a labelled scenario only, never a forecast.

## Per-entry observables

For each prospectively eligible parent entry:

- parent event key / signal date / entry date / frozen position / frozen weight;
- route and public provider;
- capture timestamp and lag from intended 00:00 UTC entry boundary;
- best bid / ask / midpoint / spread bps;
- visible entry-side depth capacity in USDT;
- whether visible entry-side capacity covers the frozen 100 USDT research notional;
- public taker round-trip fee reference;
- observable nonfunding same-book round-trip proxy = fee reference + current spread;
- headroom versus the frozen BASE10 and STRESS20 scientific cost assumptions;
- SHORT only: current funding rate, cycle and constant-current-rate 24h short burden/credit scenario;
- authenticated API used = false;
- orders created = false;
- exchange mutation = false;
- live capital = false.

No observed public friction value may modify the parent forward PnL series.

## Operational sample milestone

The parent authority already froze 10 resolved forward trades as the operational-shadow readiness milestone.

This sidecar therefore reports **10 complete prospective execution observations** as `PUBLIC_EXECUTION_SAMPLE_READY_FOR_AUDIT`.

This is a readiness milestone only:
- it is not an execution PASS;
- it does not change Tier;
- it does not authorize micro-live;
- it does not authorize production;
- it does not override the first-50 statistical gate.

If the first-50 statistical gate eventually passes, this prospective execution-shadow evidence is available for the separately required operational/execution audit.

## Firewalls

- no authenticated exchange API;
- no API key or secret;
- no POST/DELETE;
- no order placement;
- no leverage mutation;
- no wallet;
- no capital;
- no parameter change;
- no direction switch;
- no horizon change;
- no cost reduction;
- no retrospective reconstruction;
- no automatic Tier-1 promotion;
- no automatic micro-live authorization;
- no main merge.
