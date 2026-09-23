# ARQ-002-CSP-001 — FROZEN DISCOVERY AUTHORITY V0.1

Date: 2026-09-23
State at freeze: SOURCE_DATA_PASS on fixed structural probes; no ARQ-002 economic value, sweep outcome, CVD value, OI value, funding value or return has been opened.

## Identity

ARQ-002-CSP-001
CVD + Price Sweep/Reclaim Proxy + Positioning Confirmation.

One asset only: Binance USD-M BTCUSDT perpetual.

## Scientific question

Conditional on a prospectively defined BTCUSDT price sweep/reclaim proxy, does same-event aggressive-flow pressure together with contemporaneous OI/funding crowding identify a subset with stronger subsequent 5-minute reversal after realistic costs than sweep events without full confirmation?

Primary direction is REVERSAL. It may not be inverted after outcomes.

## Source authority

Official public Binance Vision only:
- daily USD-M aggTrades;
- daily USD-M BTCUSDT 1m klines;
- daily USD-M BTCUSDT metrics;
- monthly USD-M BTCUSDT fundingRate;
- published CHECKSUM files.

No REST substitution, private API, paid archive or alternate venue.

## Temporal firewall

Discovery outcomes:
- 2024-01-01T00:00:00Z through 2024-12-31T23:59:59Z only.

Warm-up source allowed:
- 2023-12-31 BTCUSDT 1m klines and metrics only, solely for the first 30-minute reference window and previous OI observation.
- 2023-12 fundingRate may be read only if needed to provide the latest funding observation strictly before an early-2024 event.

Locked:
- 2025 CONFIRMATION LOCKED.
- 2026 FINAL HOLDOUT FORBIDDEN.

Any event whose five-minute outcome would cross into 2025 is excluded.

## Full source census gate — before outcomes

All required:
- every 2024 UTC day has checksum-verified aggTrades daily object;
- every 2024 UTC day has exactly 1,440 checksum-verified 1m kline timestamps;
- every 2024 UTC day has 288 unique 5-minute metrics timestamps after exact-identical duplicate collapse only;
- no conflicting metrics duplicate group;
- all 12 2024 funding monthly objects present and checksum-verified;
- funding timestamps unique and no gap >12 hours;
- aggTrade aggregate IDs unique inside each daily object;
- aggTrade buyer-maker flag parseable;
- all timestamps strictly <2025-01-01 for Discovery source;
- warm-up objects limited to the frozen 2023-12 boundary source.

Any missing required 2024 object => SOURCE_DATA_INSUFFICIENT and no economic Discovery.

## Event clock

All event construction uses 1-minute UTC bars.

For minute M with open timestamp t:
- reference window = the immediately preceding 30 completed one-minute candles t-30m ... t-1m;
- H30 = maximum HIGH of those 30 candles;
- L30 = minimum LOW of those 30 candles.

### High sweep/reclaim proxy
A short-reversal baseline event occurs if:
- HIGH_M > H30, and
- CLOSE_M < H30.

### Low sweep/reclaim proxy
A long-reversal baseline event occurs if:
- LOW_M < L30, and
- CLOSE_M > L30.

Strict inequalities only.

If both high-sweep and low-sweep conditions occur in the same minute:
- classify AMBIGUOUS_BOTH_SIDES;
- exclude.

No breach magnitude threshold, wick/body threshold, ATR filter or volume threshold.

Event becomes knowable only after minute M closes.

## CVD / aggressive-flow definition

Use every BTCUSDT aggTrade whose exchange timestamp lies inside minute M:
[t, t+60s).

For each aggregate trade:
- quote notional = price × quantity;
- if `isBuyerMaker == false`: signed notional = +quote notional (buyer aggressor);
- if `isBuyerMaker == true`: signed notional = -quote notional (seller aggressor).

EVENT_CVD = sum(signed notional).
EVENT_TOTAL_AGGRESSIVE_NOTIONAL = sum(abs(signed notional)).
EVENT_CVD_RATIO = EVENT_CVD / EVENT_TOTAL_AGGRESSIVE_NOTIONAL.

If total aggressive notional <=0: event ineligible.

No rolling or cumulative CVD prior to M is used in the primary rule.

### CVD confirmation
For HIGH sweep/short reversal:
- EVENT_CVD_RATIO > 0.

For LOW sweep/long reversal:
- EVENT_CVD_RATIO < 0.

Interpretation: aggressive flow pushes through the extreme but price reclaims, consistent with trapped aggressors.

Zero CVD ratio = not confirmed.

No magnitude threshold.

## OI confirmation

Metrics source cadence is frozen at 5 minutes.

At event close E=t+60s:
- OI_now = latest valid metrics row with create_time <= E;
- OI_prev = immediately preceding valid metrics row exactly 5 minutes earlier.

Require exact 5-minute adjacency.
If either row is missing: OI confirmation unavailable and full confirmation fails for that event.

OI_CHANGE = ln(OI_now / OI_prev).

OI crowding confirmation for BOTH directions:
- OI_CHANGE > 0.

No magnitude threshold.

## Funding confirmation

Funding source cadence is approximately 8 hours.

At event close E:
- FUNDING = latest official funding observation timestamp <= E.

Staleness must be <= 8 hours + 5 minutes.
If no valid observation: funding confirmation unavailable.

HIGH sweep / short reversal:
- FUNDING > 0.

LOW sweep / long reversal:
- FUNDING < 0.

Zero funding = not confirmed.

No magnitude threshold.

## Frozen ablation

A = all non-ambiguous sweep/reclaim baseline events.
B = A + correct CVD sign.
C = B + OI_CHANGE >0.
D = C + correct funding sign.

D is FULL CONFIRMATION.

D-rejected = baseline A event not satisfying D.

No component may be reordered or replaced after outcomes.

## Entry and outcome

Event minute M is fully closed before entry.

Entry:
- OPEN of minute M+1.

Primary exit:
- CLOSE of minute M+5.

This spans exactly five complete one-minute candles:
M+1, M+2, M+3, M+4, M+5.

Signed gross reversal return:
- LOW sweep / long: +ln(exit / entry)
- HIGH sweep / short: -ln(exit / entry)

No intrabar stop/TP.

## Costs

Round-trip:
- LOW10 = 10 bps
- BASE14 = 14 bps
- STRESS20 = 20 bps

Primary economic gate uses BASE14.
STRESS20 must also be positive.

No fee/slippage reduction after outcomes.

## Discovery inference

Primary population:
all D-confirmed events in 2024.

Primary statistic:
unweighted arithmetic mean BASE14 net return.

UTC-day block bootstrap:
- sample complete UTC dates with replacement;
- every sampled date contributes all D-confirmed events on that date;
- number sampled dates equals number unique eligible dates;
- 10,000 repetitions;
- seed 2002001;
- percentile 95% CI.

## Frozen Discovery gates — ALL required

1. full source census PASS;
2. D-confirmed N >= 200;
3. D-confirmed events occur on >= 60 unique UTC days;
4. BASE14 pooled mean > 0;
5. STRESS20 pooled mean > 0;
6. mean(D-confirmed BASE14) - mean(D-rejected BASE14) > 0;
7. UTC-day bootstrap 95% lower bound for D-confirmed BASE14 > 0;
8. HIGH-sweep/short D-confirmed BASE14 mean > 0;
9. LOW-sweep/long D-confirmed BASE14 mean > 0;
10. at least 7 of 12 calendar-month D-confirmed BASE14 means > 0;
11. remove best ceil(1%) D-confirmed events by BASE14 return; remaining mean > 0;
12. no single calendar month contributes >25% of D-confirmed events.

If either D-confirmed or D-rejected is empty, gate 6 fails.

## Deterministic robustness semantics

Best 1%:
- remove max(1, ceil(0.01*N)) highest BASE14 observations;
- tie break: event timestamp ascending.

Monthly positivity:
- months with zero D-confirmed observations count as non-positive for gate 10.

Month concentration:
- max(month_N / total_N).

## Terminal states

- DISCOVERY_SURVIVES_NOT_EDGE
- DISCOVERY_FAIL_NO_PROMOTION
- SOURCE_DATA_INSUFFICIENT
- SOURCE_PROVENANCE_FAIL
- TECHNICAL_FAIL_CLOSED

Discovery survival is NOT a Diamond, not a live-trading edge and not authorization for 2025.

## Hard no-rescue

After any 2024 outcome is opened, do not:
- change 30m reference window;
- add breach threshold;
- change CVD sign or add magnitude threshold;
- change OI/funding sign;
- switch reversal to continuation;
- change 5m horizon;
- change costs;
- subset hours/days/months;
- add altcoins;
- remove losing side;
- open 2025 after Discovery failure.

## Governance

No live trading.
No orders.
No wallet.
No exchange mutation.
No main merge.
No deployment.
