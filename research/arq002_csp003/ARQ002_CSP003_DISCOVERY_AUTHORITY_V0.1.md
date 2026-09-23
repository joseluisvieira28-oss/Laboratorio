# ARQ-002-CSP-003 — CVD + SWEEP/RECLAIM + POSITIONING — VALIDITY-MASK DISCOVERY AUTHORITY V0.1

Date: 2026-09-23
Branch: `arq002-csp003-validity-mask-v0.1`
State: FROZEN_PRE_DISCOVERY / RESEARCH_ONLY / OUTCOME_BLIND FOR CSP-003

## Lineage

Parent archaeology hit:
ARQ-002 — CVD + LIQUIDITY SWEEPS + POSITIONING CONFIRMATION.

Prior source attempts:
- CSP-001: SOURCE_DATA_INSUFFICIENT because 127 metrics timestamps were missing.
- CSP-002: TECHNICAL_FAIL_CLOSED because the source mask treated timestamp presence as sufficient, but 305 present metrics rows had non-positive sum_open_interest. Partial monthly economic artifacts from CSP-002 are intentionally not inspected or adjudicated and are not admissible evidence for CSP-003.

CSP-003 is a NEW source-validity child. Its economic hypothesis, event rule, direction, horizon, costs and promotion gates are unchanged from CSP-002.

## Scientific question

Conditional on a prospectively defined BTCUSDT price sweep/reclaim proxy, does same-event aggressive-flow pressure together with contemporaneous OI/funding crowding identify a subset with stronger subsequent 5-minute reversal after realistic costs than sweep events without full confirmation?

Primary direction: REVERSAL.

## Source authority

Official Binance Vision only:
- BTCUSDT USD-M daily aggTrades;
- BTCUSDT USD-M daily 1m klines;
- BTCUSDT USD-M daily metrics;
- BTCUSDT USD-M monthly fundingRate;
- published CHECKSUM sidecars.

No REST fallback, private API, alternate venue, paid data, interpolation or reconstruction.

## Frozen source evidence

The following source-only evidence was completed before CSP-003 outcomes:
- full 2024 source census: run 35908982717, receipt SHA256 182b1a501a9b51727e8e01a25919f6a74bcf24602bd3944727aed5bc9b47c1f7;
- OI validity diagnostic: run 35910417295, receipt SHA256 d459acd54ab5dffa3dedb0d0a397a19e5ff7415289f7e8302c7bf61b42b7ff62.

Source facts:
- 366/366 2024 aggTrades objects verified;
- 530,973,404 aggregate-trade rows structurally scanned;
- 366/366 1m kline objects verified;
- 12/12 2024 funding monthly objects verified;
- 105,408 expected 5-minute metrics slots;
- 127 missing metrics timestamps;
- 305 present rows with non-positive sum_open_interest;
- zero non-finite/non-numeric invalid OI rows in the diagnostic;
- total unavailable OI slots = 432;
- usable valid-positive OI slots = 104,976.

No return, sweep outcome, CVD result, funding result or economic verdict from CSP-002 is admissible to CSP-003.

## OI validity mask

An OI slot is VALID if and only if ALL are true:
1. the exact official metrics timestamp exists;
2. duplicate timestamp rows, if any, are byte/field-identical after parsing;
3. sum_open_interest parses as finite numeric;
4. sum_open_interest > 0.

Otherwise the slot is UNAVAILABLE_SOURCE.

For event minute M with open timestamp t and event close E=t+60s:
- OI_slot_now = greatest exact UTC five-minute boundary <= E;
- OI_slot_prev = OI_slot_now - 5 minutes.

The event is source-eligible for OI only when BOTH slots are VALID.

No fallback to older data.
No zero replacement.
No absolute value.
No epsilon repair.
No interpolation/forward-fill/back-fill.

The exact 2024 unavailable-slot mask is frozen by per-month SHA256 before CSP-003 outcomes.

## Temporal firewall

Discovery:
- 2024 only.

Warm-up:
- 2023-12-31 klines/metrics and 2023-12 funding only for causal boundary state.

Locked:
- 2025 CONFIRMATION LOCKED.
- 2026 FINAL HOLDOUT FORBIDDEN.

Any 5-minute outcome crossing into 2025 is excluded.

## Sweep/reclaim proxy

For 1m candle M open t:
- reference = immediately preceding 30 completed 1m candles;
- H30 = max reference HIGH;
- L30 = min reference LOW.

HIGH sweep / short reversal:
- HIGH_M > H30;
- CLOSE_M < H30.

LOW sweep / long reversal:
- LOW_M < L30;
- CLOSE_M > L30.

Strict inequalities.
Both sides in same minute => AMBIGUOUS_BOTH_SIDES => exclude.

No breach magnitude, wick/body, ATR or volume threshold.

## CVD confirmation

For aggTrades timestamped in [t,t+60s):
- quote notional = price × quantity;
- isBuyerMaker=false => +notional;
- isBuyerMaker=true => -notional.

CVD_RATIO = sum(signed notional) / sum(abs signed notional).

If denominator <=0: event ineligible.

HIGH sweep / short:
- CVD_RATIO > 0.

LOW sweep / long:
- CVD_RATIO < 0.

No magnitude threshold.

## OI confirmation

Only source-eligible valid-positive OI slots are used.

OI_CHANGE = ln(OI_now / OI_prev).

Both directions:
- OI_CHANGE > 0.

No magnitude threshold.

## Funding confirmation

At event close:
- latest official funding observation <= event close;
- max staleness = 8h + 5m.

HIGH sweep / short:
- FUNDING > 0.

LOW sweep / long:
- FUNDING < 0.

Zero/unavailable = not confirmed.

## Ablation

A = source-eligible non-ambiguous sweep/reclaim event with valid aggTrade notional.
B = A + correct CVD sign.
C = B + OI_CHANGE >0.
D = C + correct funding sign.

D = full confirmation.
D-rejected = A not satisfying D.

## Entry/outcome

Entry = OPEN of M+1.
Exit = CLOSE of M+5.

Exactly five complete 1m candles.

Gross signed reversal:
- LOW/long: +ln(exit/entry);
- HIGH/short: -ln(exit/entry).

No stop/TP.

## Costs

Round trip:
- LOW10 = 10 bps;
- BASE14 = 14 bps;
- STRESS20 = 20 bps.

Primary gate uses BASE14.
STRESS20 must also be positive.

## Discovery inference

Primary population = all D-confirmed CSP-003 events in 2024.

Unweighted arithmetic mean BASE14.

UTC-day bootstrap:
- complete UTC-day blocks;
- 10,000 reps;
- seed 2002001;
- percentile 95% CI.

## Frozen Discovery gates — ALL required

1. source validity mask PASS;
2. D-confirmed N >=200;
3. D-confirmed events on >=60 unique UTC days;
4. pooled BASE14 mean >0;
5. pooled STRESS20 mean >0;
6. mean(D-confirmed BASE14) - mean(D-rejected BASE14) >0;
7. UTC-day bootstrap 95% lower bound >0;
8. HIGH-sweep/short D-confirmed BASE14 mean >0;
9. LOW-sweep/long D-confirmed BASE14 mean >0;
10. >=7 of 12 calendar-month D-confirmed BASE14 means >0;
11. remove best max(1,ceil(1%*N)) D-confirmed events; remaining BASE14 mean >0;
12. no single month contributes >25% of D-confirmed observations.

Best-1% tie-break:
- BASE14 descending;
- timestamp ascending.

Months with zero D-confirmed = non-positive.

## Terminal states

- DISCOVERY_SURVIVES_NOT_EDGE
- DISCOVERY_FAIL_NO_PROMOTION
- SOURCE_PROVENANCE_FAIL
- TECHNICAL_FAIL_CLOSED

## Hard no-rescue

After CSP-003 opens any 2024 outcome:
- no source-mask change;
- no dropping OI/funding/CVD component;
- no stale OI;
- no sign inversion;
- no continuation switch;
- no threshold/window/horizon/cost change;
- no time/month subgrouping;
- no added assets;
- no 2025 opening after failure.

## Governance

No live trading.
No orders.
No wallet.
No exchange mutation.
No main merge.
No deployment.
