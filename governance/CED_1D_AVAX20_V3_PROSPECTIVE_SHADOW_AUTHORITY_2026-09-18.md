# CED-1D AVAX20 — V3 PROSPECTIVE SHADOW / PREFLIGHT AUTHORITY — 2026-09-18

**Status:** FROZEN / ARMED PROSPECTIVELY / NON-LIVE  
**Candidate:** `CED1D-0031` — AVAXUSDT Momentum 20D CONTINUATION H1D  
**Parent current V3 state:** TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE  
**Purpose:** collect genuinely prospective operational and economic evidence required for any later Tier-1 adjudication.

This document authorizes **public-data, non-live shadow research only**. It does not authorize real orders, exchange mutation, wallets, capital, leverage, alerts/webhooks that execute, or production.

## 1. Prospective firewall

The shadow rules are frozen on 2026-09-18 before the first eligible prospective signal completion.

Earliest eligible signal completion:
- `2026-09-19T00:00:00Z`

That is the completion boundary for UTC signal day:
- `2026-09-18`

Earliest eligible reference entry:
- `2026-09-19T00:01:00Z`

No signal, entry, exit, PnL or execution outcome with signal completion before `2026-09-19T00:00:00Z` may enter the shadow evidence set.

### Warm-up exception

After this authority is frozen, the runner may read only the minimum pre-boundary 2026 price history required to compute the immutable 20-calendar-day momentum signal and validate its exact daily path.

Warm-up rows are INPUT ONLY.
They may not be scored as shadow trades, used as a validation block, or inspected to select/tune any parameter.

No pre-freeze 2026 trade outcome may be backfilled.

## 2. Immutable signal

No changes from CED1D-0031:
- symbol: AVAXUSDT
- venue research surface: Binance USD-M perpetual futures
- lookback: 20 calendar days
- signal: `ln(close_D / close_D-20)`
- direction: CONTINUATION
- position direction: sign(momentum)
- exact daily path required
- signal completion: UTC day boundary
- reference entry: D+1 00:01 UTC exact 1m open
- reference exit: entry + 1 calendar day, exact 00:01 UTC 1m open
- one active event configuration
- overlap semantics unchanged
- no stops, targets, discretionary filters or regime switches

No asset, horizon, lookback, timing, side, threshold or event rule may change after prospective observations begin.

## 3. Shadow data tracks

Two tracks must be preserved simultaneously.

### A. Reference-comparability track

Purpose: exact comparison to the independent 2025 OOS lineage.

For every eligible prospective event:
- preserve original reference entry/exit semantics;
- preserve actual funding using the same conservative, source-supported treatment;
- BASE nonfunding cost floor: **14 bps round trip**;
- STRESS nonfunding cost floor: **20 bps round trip**.

This track must never be replaced by execution-proxy economics.

### B. 100-USDT execution-research track

Purpose: operational realism at the exact V3-promoted scope.

Immutable notional:
- **100 USDT per leg**

aggTrades proxy:
- same frozen 5,000 ms same-side observed-taker-print methodology as the 2025 execution audit;
- BASE taker fee: 4 bps/fill = 8 bps RT;
- STRESS taker fee: 5 bps/fill = 10 bps RT;
- no VIP/BNB/Taker Program discount;
- no maker assumption;
- no widening of the 5-second window;
- observed-print misses remain misses and are never silently deleted.

bookDepth corroboration:
- same frozen ±1% capacity semantics;
- BUY -> +1% ask-side cumulative band;
- SELL -> -1% bid-side cumulative band;
- latest snapshot <= reference time;
- age <=60 seconds;
- cumulative notional >=100 USDT;
- no exact-BBO/fill-price inference from bookDepth.

The historical 2025 aggTrades print-visibility FAIL remains preserved and is not reset by the prospective shadow.

## 4. Minimum prospective evidence before adjudication

Expected frozen cadence from the 2025 OOS is approximately 357 events / 51 complete signal weeks = 7 events/week.

Therefore the shadow evidence gate is frozen as BOTH:
- at least **60 completed prospective shadow events**, and
- at least **8 complete UTC signal weeks**.

If 60 events are not reached after 8 weeks, continue until 60.
If 60 events occur before 8 complete weeks, continue until 8 complete weeks.

No early Tier-1 decision is allowed.

## 5. Operational integrity gates

The shadow/preflight is operationally valid only if:
- 100% of included signals are deterministically generated from the frozen CED1D-0031 rule;
- no eligible event is manually deleted or shifted;
- no source failure is silently omitted;
- all accessed data are public/read-only;
- bookDepth valid-snapshot coverage >=99% of all required legs;
- bookDepth 100-USDT capacity coverage >=99% of all required legs;
- every active shadow month has >=95% bookDepth capacity coverage;
- no 2026 pre-boundary trade is included;
- no live order/exchange mutation occurs.

aggTrades observed-print visibility remains a mandatory reported fragility metric, but the already-frozen composite structure is retained: bookDepth is the hard all-leg capacity corroboration and aggTrades supplies execution-price/latency economics on observable complete pairs.

For execution-economic adjudication there must be at least **50 complete prospective aggTrades proxy pairs**. Fewer than 50 is `SHADOW_EXECUTION_SAMPLE_INSUFFICIENT`, not a negative market verdict.

## 6. Prospective economic gates

After the minimum 60-event / 8-week shadow sample is complete:

### Reference-comparability track
Required for a positive forward adjudication:
- BASE funded mean > 0
- BASE funded PF > 1
- STRESS funded mean >= 0
- at least 50% of complete UTC shadow weeks BASE-positive

### Execution track
On complete observed-print proxy pairs:
- BASE executable funded mean > 0
- BASE executable funded PF > 1
- STRESS executable funded mean >= 0
- median leg latency <=1,000 ms
- p95 leg latency <=5,000 ms
- mean total nonfunding BASE proxy <=14 bps RT
- p95 total nonfunding BASE proxy <=20 bps RT

### Concentration
On the prospective shadow economic ledger:
- no single month >30% of absolute BASE executable PnL
- top-5 events <=20% of absolute BASE executable PnL
- no single day >10% of absolute BASE executable PnL

Negative execution drag remains negative; no clipping.

## 7. Adjudication routing — frozen before shadow outcomes

After minimum sample:

### TIER1_ADJUDICATION_ELIGIBLE
Only if:
- all operational gates PASS;
- reference-comparability economic gates PASS;
- execution-economic gates PASS;
- concentration gates PASS;
- no material provenance/execution contradiction appears.

This label is **not an automatic Tier 1 promotion**. A separate V3 adjudication must still decide Tier 1.

### TIER2_RETAINED_FORWARD_FRAGILITY
If the forward block is mixed/uncertain but not materially contradictory, or an execution diagnostic is fragile while economic sign remains defensible.

### SHADOW_BLOCKED_OR_INSUFFICIENT
If public source integrity or minimum execution-proxy sample cannot be established. This is not NO_EDGE.

### MATERIAL_FORWARD_CONTRADICTION
If, after the full minimum shadow sample, the exact reference candidate is materially negative under BASE costs with PF materially below 1, or the prospective block otherwise destroys the expected sign under clean data.

No rescue is permitted. Such a result must trigger a fresh V3 re-adjudication and may demote/reject the exact candidate.

## 8. No automatic capital escalation

The following remain forbidden under this shadow authority:
- real-money trading
- test orders
- wallets
- exchange account mutation
- leverage
- auto-execution alerts/webhooks
- increasing notional above 100 USDT for research inference
- main merge

A later Tier-1 scientific decision still would not authorize production capital.

## 9. First eligible boundary

Because this authority is frozen during 2026-09-18 UTC before the next daily completion boundary, the first eligible prospective signal completion is fixed at:

`2026-09-19T00:00:00Z`

First possible reference entry:

`2026-09-19T00:01:00Z`

Any observation earlier than that is ineligible for shadow performance evidence.

**Final state after this freeze:** AVAX20 remains V3 Tier-2 / Quase Diamante and advances to prospectively armed M6 shadow research with zero resolved post-freeze events at freeze time.
