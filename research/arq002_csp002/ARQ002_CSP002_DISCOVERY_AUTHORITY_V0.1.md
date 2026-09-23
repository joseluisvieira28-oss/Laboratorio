# ARQ-002-CSP-002 — CVD + SWEEP/RECLAIM + POSITIONING — SOURCE-MASK DISCOVERY AUTHORITY V0.1

Date: 2026-09-23
Branch: `arq002-csp002-source-mask-v0.1`
State: FROZEN_PRE_SOURCE / RESEARCH_ONLY / OUTCOME_BLIND

## Lineage and reason for new LAB_ID

Parent archaeology hit:
ARQ-002 — CVD + LIQUIDITY SWEEPS + POSITIONING CONFIRMATION.

Direct predecessor:
ARQ-002-CSP-001.

CSP-001 never opened economic outcomes. Its fixed structural source probe passed, but its full 2024 source census closed SOURCE_DATA_INSUFFICIENT because Binance Vision BTCUSDT metrics were not a complete 288/288 five-minute grid on exactly two UTC dates:
- 2024-02-16: 125 missing five-minute slots, 13:35Z through 23:55Z;
- 2024-10-28: 2 missing five-minute slots, 16:25Z and 16:30Z.

All diagnostics were source-only.

CSP-002 is a NEW prospective child authorized before any ARQ-002 economic value, sweep outcome, CVD value, OI value, funding value or return has been opened.

## Scientific question

Unchanged from CSP-001:

Conditional on a prospectively defined BTCUSDT price sweep/reclaim proxy, does same-event aggressive-flow pressure together with contemporaneous OI/funding crowding identify a subset with stronger subsequent 5-minute reversal after realistic costs than sweep events without full confirmation?

Primary direction is REVERSAL. It may not be inverted after outcomes.

## Anti-duplication

This lab does not reopen:
- generic taker imbalance / SCL-AGG-002;
- LL-0017 positioning;
- liquidation-pressure;
- order-book refill;
- L2-RESILIENCY replenishment.

The event prerequisite remains a deterministic PRICE SWEEP/RECLAIM PROXY. It is not represented as true L2 depletion, stop inventory or liquidation.

## Asset

Exactly:
- Binance USD-M BTCUSDT perpetual.

No cross-asset search.

## Source authority

Official public Binance Vision only:
- daily BTCUSDT USD-M aggTrades;
- daily BTCUSDT USD-M 1m klines;
- daily BTCUSDT USD-M metrics;
- monthly BTCUSDT USD-M fundingRate;
- published CHECKSUM sidecars.

No REST fallback, private API, alternate venue or paid data.

## Temporal firewall

Discovery outcomes:
- 2024-01-01T00:00:00Z through 2024-12-31T23:59:59Z only.

Warm-up:
- 2023-12-31 1m klines + metrics;
- 2023-12 fundingRate only as required for first-2024 causal state.

Locked:
- 2025 CONFIRMATION LOCKED;
- 2026 FINAL HOLDOUT FORBIDDEN.

Any event whose five-minute outcome crosses into 2025 is excluded.

## CSP-002 source-mask rule

All 2024 aggTrades, 1m kline and funding objects remain mandatory.

Metrics are handled with an event-level deterministic availability mask:

1. Every observed metrics timestamp must be on the exact UTC five-minute grid.
2. Exact-identical duplicate rows may be collapsed.
3. Any conflicting duplicate timestamp group = SOURCE_PROVENANCE_FAIL.
4. Missing metrics timestamps are persisted exactly in a source-mask receipt.
5. No missing OI value is interpolated, forward-filled, backward-filled, averaged, reconstructed or substituted.

For an event minute M with open timestamp t and event close E=t+60s:

- OI_slot_now = the greatest exact UTC five-minute boundary <= E.
- OI_slot_prev = OI_slot_now - 5 minutes.

The event may use OI only if BOTH exact timestamps exist in the official metrics source.

If either timestamp is absent:
- event state = INELIGIBLE_SOURCE_MASK;
- event is excluded before any OI value, funding value, CVD confirmation or future return is evaluated for scientific scoring.

Critically, the runner may NOT fall back to an older "latest valid" OI row across a gap.

## Full source census gate — before outcomes

All required:
- all 366 2024 aggTrades daily objects present and checksum verified;
- aggregate-trade IDs strictly increasing within each daily object;
- buyer-maker boolean parseable;
- all 366 2024 1m kline objects present and checksum verified;
- exactly 1,440 kline timestamps per UTC day;
- every observed metrics daily object present and checksum verified;
- metrics observed timestamps on exact five-minute grid;
- zero conflicting metrics duplicate groups;
- exact list of missing metrics five-minute timestamps persisted;
- all 12 2024 monthly fundingRate objects present and checksum verified;
- funding timestamps unique;
- no funding gap >12 hours;
- warm-up restricted to frozen 2023-12 boundary source;
- no timestamp >=2025-01-01 in Discovery source.

No minimum global metrics-coverage percentage is fitted. Event-level availability and the later frozen sample-size gates determine whether the experiment is adequately populated.

## Event clock and sweep/reclaim proxy

Unchanged from CSP-001.

For minute M with open timestamp t:
- reference window = immediately preceding 30 completed 1m candles t-30m ... t-1m;
- H30 = max HIGH of reference window;
- L30 = min LOW of reference window.

HIGH sweep / short-reversal baseline:
- HIGH_M > H30;
- CLOSE_M < H30.

LOW sweep / long-reversal baseline:
- LOW_M < L30;
- CLOSE_M > L30.

Strict inequalities.

If both occur in the same minute:
- AMBIGUOUS_BOTH_SIDES;
- exclude.

No breach threshold, wick/body filter, ATR filter or volume threshold.

## CVD / aggressive-flow confirmation

Use every BTCUSDT aggTrade with exchange timestamp in [t,t+60s).

For each aggregate trade:
- quote notional = price × quantity;
- isBuyerMaker=false => +quote notional;
- isBuyerMaker=true => -quote notional.

EVENT_CVD = signed-notional sum.
EVENT_TOTAL_AGGRESSIVE_NOTIONAL = absolute-notional sum.
EVENT_CVD_RATIO = EVENT_CVD / EVENT_TOTAL_AGGRESSIVE_NOTIONAL.

If total <=0, event ineligible.

HIGH sweep / short reversal:
- CVD_RATIO > 0.

LOW sweep / long reversal:
- CVD_RATIO < 0.

Zero = not confirmed.
No magnitude threshold.

## OI confirmation

Only after the event passes the CSP-002 source mask.

OI_CHANGE = ln(OI_now / OI_prev).

For BOTH reversal directions:
- OI_CHANGE > 0.

No magnitude threshold.

## Funding confirmation

At event close E:
- use latest official funding observation timestamp <= E;
- staleness <= 8 hours + 5 minutes.

HIGH sweep / short reversal:
- FUNDING > 0.

LOW sweep / long reversal:
- FUNDING < 0.

Zero or unavailable = not confirmed.
No magnitude threshold.

## Frozen ablation

A = eligible non-ambiguous sweep/reclaim baseline events after source mask.
B = A + correct CVD sign.
C = B + OI_CHANGE > 0.
D = C + correct funding sign.

D = FULL CONFIRMATION.
D-rejected = eligible A event not satisfying D.

No component may be reordered/replaced after outcomes.

## Entry/outcome

Event M fully closes before entry.

Entry:
- OPEN of minute M+1.

Exit:
- CLOSE of minute M+5.

Exactly five complete 1m candles.

Signed gross reversal:
- LOW sweep / long = +ln(exit/entry);
- HIGH sweep / short = -ln(exit/entry).

No stop/TP.

## Costs

Round-trip:
- LOW10 = 10 bps;
- BASE14 = 14 bps;
- STRESS20 = 20 bps.

Primary economic gate = BASE14.
STRESS20 must also be >0.

## Discovery inference

Primary population:
- all D-confirmed source-eligible events in 2024.

Primary statistic:
- unweighted arithmetic mean BASE14.

UTC-day bootstrap:
- sample complete UTC dates with replacement;
- each selected date contributes all D-confirmed events;
- sampled date count equals unique eligible D-confirmed dates;
- 10,000 reps;
- seed 2002001;
- percentile 95% CI.

## Frozen Discovery gates — ALL required

1. CSP-002 full source census PASS;
2. D-confirmed N >= 200;
3. D-confirmed events on >=60 unique UTC days;
4. BASE14 pooled mean >0;
5. STRESS20 pooled mean >0;
6. mean(D-confirmed BASE14) - mean(D-rejected BASE14) >0;
7. UTC-day bootstrap 95% lower bound >0;
8. HIGH-sweep/short D-confirmed BASE14 mean >0;
9. LOW-sweep/long D-confirmed BASE14 mean >0;
10. >=7 of 12 calendar-month D-confirmed BASE14 means >0;
11. remove best max(1,ceil(1%*N)) D-confirmed events; remaining BASE14 mean >0;
12. no single calendar month contributes >25% of D-confirmed events.

If confirmed or rejected set is empty, gate 6 fails.

Best-1% tie-break:
- BASE14 descending, then event timestamp ascending.

Months with zero D-confirmed observations count non-positive for gate 10.

## Terminal states

- DISCOVERY_SURVIVES_NOT_EDGE
- DISCOVERY_FAIL_NO_PROMOTION
- SOURCE_DATA_INSUFFICIENT
- SOURCE_PROVENANCE_FAIL
- TECHNICAL_FAIL_CLOSED

Discovery survival is not a trading edge and does not open 2025.

## Hard no-rescue

After any 2024 outcome is opened, do not:
- alter source-mask semantics;
- permit stale OI fallback;
- change 30m sweep window;
- add breach/wick/ATR/volume thresholds;
- invert CVD sign;
- alter OI/funding sign;
- switch reversal to continuation;
- alter 5m horizon or costs;
- subset hours/days/months;
- add assets;
- remove losing side;
- open 2025 after Discovery failure.

## Governance

No live trading.
No orders.
No wallet.
No exchange mutation.
No main merge.
No deployment.
