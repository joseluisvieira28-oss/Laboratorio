# ARQ-002-CSP-003 — CLEAN DISCOVERY 2022 / REPLICATION 2023 — AUTHORITY V0.1

Date: 2026-09-23
Branch: `arq002-csp003-clean-2022-2023-v0.1`
State: FROZEN_PRE_SOURCE / RESEARCH_ONLY / OUTCOME_BLIND FOR 2022-2023

## Why a new LAB_ID

CSP-002 opened partial 2024 monthly outcomes before a source-validity issue was discovered in Binance metrics OI values. Exact CSP-002 is closed and may not be repaired post-outcome.

CSP-003 uses an outcome-unopened period:
- Discovery: calendar 2022
- Replication: calendar 2023, released only if 2022 survives
- 2024: excluded from scientific scoring under this LAB_ID
- 2025/2026: locked/forbidden

No 2024 result, sign, threshold, subgroup, month or side may influence CSP-003.

## Mechanism — unchanged

Asset: Binance USD-M BTCUSDT perpetual.

Question:
Conditional on a deterministic price sweep/reclaim proxy, does trapped-aggressor CVD together with OI expansion and same-direction funding crowding identify a subset with stronger subsequent 5-minute REVERSAL after costs than rejected sweep events?

Primary direction remains REVERSAL.

## Sources

Official Binance Vision only:
- daily BTCUSDT USD-M 1m klines;
- daily BTCUSDT USD-M aggTrades;
- daily BTCUSDT USD-M metrics;
- monthly BTCUSDT USD-M fundingRate;
- published CHECKSUM sidecars.

No REST fallback, private API, alternate venue or paid archive.

Warm-up for 2022:
- 2021-12-31 1m klines + metrics;
- 2021-12 fundingRate only as required for causal state.

## OI validity mask — frozen before any 2022/2023 outcome

For every observed metrics row:
- timestamp must be exact UTC 5-minute grid;
- exact-identical duplicates may collapse;
- conflicting duplicate group = SOURCE_PROVENANCE_FAIL.

An OI slot is VALID only if `sum_open_interest` is:
- numeric;
- finite;
- strictly > 0.

Otherwise classify one of:
- MISSING;
- NONNUMERIC;
- NONFINITE;
- NONPOSITIVE.

For event minute M with close E=t+60s:
- OI_slot_now = greatest exact UTC 5m boundary <= E;
- OI_slot_prev = OI_slot_now - 5m.

Event may proceed beyond source eligibility only if BOTH exact slots exist and BOTH OI values are VALID.

Any failure => `INELIGIBLE_OI_SOURCE_MASK`.

No forward-fill, backward-fill, interpolation, stale fallback, averaging, reconstruction or substitution.

## Sweep/reclaim event

For 1m event candle M open at t:
- reference = immediately preceding 30 completed 1m candles;
- H30 = max HIGH;
- L30 = min LOW.

HIGH sweep / short reversal:
- HIGH_M > H30
- CLOSE_M < H30

LOW sweep / long reversal:
- LOW_M < L30
- CLOSE_M > L30

Both sides in one minute => AMBIGUOUS_BOTH_SIDES, excluded.
Strict inequalities; no wick/ATR/volume/breach threshold.

## CVD confirmation

Use all aggTrades in [t,t+60s):
- quote notional = price × quantity
- isBuyerMaker=false => +notional
- isBuyerMaker=true => -notional
- CVD_RATIO = signed sum / absolute-notional sum

HIGH sweep / short reversal: CVD_RATIO > 0
LOW sweep / long reversal: CVD_RATIO < 0

Zero or empty = not confirmed.
No magnitude threshold.

## OI confirmation

After source eligibility:
- OI_CHANGE = ln(OI_now / OI_prev)
- confirmation for BOTH directions: OI_CHANGE > 0

No magnitude threshold.

## Funding confirmation

At event close E:
- latest official funding timestamp <= E
- staleness <= 8h05m

HIGH sweep / short reversal: FUNDING > 0
LOW sweep / long reversal: FUNDING < 0

Zero/unavailable = not confirmed.

## Ablation

A = source-eligible non-ambiguous sweep/reclaim
B = A + CVD sign
C = B + OI_CHANGE > 0
D = C + funding sign

D = full confirmation.
D-rejected = eligible A event not satisfying D.

## Entry / outcome / costs

Entry = OPEN of M+1.
Exit = CLOSE of M+5.
Exactly five complete 1m candles.

Signed gross reversal:
- LOW sweep long = +ln(exit/entry)
- HIGH sweep short = -ln(exit/entry)

Round-trip costs:
- LOW10 = 10 bps
- BASE14 = 14 bps
- STRESS20 = 20 bps

No stop/TP.

## 2022 Discovery gates — ALL required

1. source census PASS;
2. D N >= 200;
3. D unique UTC days >= 60;
4. D BASE14 mean > 0;
5. D STRESS20 mean > 0;
6. mean(D BASE14) - mean(D-rejected BASE14) > 0;
7. UTC-day bootstrap 95% lower bound > 0;
8. HIGH-sweep/short D BASE14 mean > 0;
9. LOW-sweep/long D BASE14 mean > 0;
10. >=7/12 monthly D BASE14 means > 0;
11. remove best max(1,ceil(1%*N)) D events and mean remains > 0;
12. max monthly concentration <= 25%.

Bootstrap:
- complete UTC-day blocks
- 10,000 reps
- seed 2002001
- percentile 95% CI

Best-1% tie break: BASE14 descending, then event timestamp ascending.
Months with zero D count non-positive.

Failure => DISCOVERY_FAIL_NO_PROMOTION and 2023 remains unopened.

## 2023 replication — pre-frozen but locked

Only if every 2022 Discovery gate passes:
- run identical source rules, mechanism, costs, bootstrap and 12 gates on calendar 2023.
- no retuning between years.

All replication gates pass => REPLICATION_SURVIVES_NOT_EDGE.
Any fail => REPLICATION_FAIL_NO_PROMOTION.

Even replication survival is not live-trading authority.

## Hard no-rescue

After 2022 outcomes:
- no source-mask change;
- no continuation switch;
- no threshold change;
- no horizon/cost change;
- no subperiod/hour/day mining;
- no side removal;
- no additional asset;
- no 2023 access after 2022 failure.

## Governance

No 2024 scoring.
No 2025/2026.
No live trading/orders/wallets/exchange mutation.
No main merge/deployment.
