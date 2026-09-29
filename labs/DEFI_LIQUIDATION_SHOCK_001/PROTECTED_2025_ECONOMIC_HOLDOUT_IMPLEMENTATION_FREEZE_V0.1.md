# DEFI-LIQUIDATION-SHOCK-001 — 2025 ECONOMIC HOLDOUT IMPLEMENTATION FREEZE V0.1

Date: 2026-09-29
Status: FROZEN / BEFORE 2025 MARKET OUTCOMES

## Required authorities
- OOS_ADJUDICATION_LOCK_V0.1.json = SURVIVES_OOS
- DIRECTION_SOURCE_AUDIT_LOCK_V0.1.json = DIRECTION_SOURCE_ROLE_AUDIT_PASS
- STRATEGY_TRANSLATION_FREEZE_V0.1.md
- EXECUTION_COST_FREEZE_V0.1.md
- MEXC_API_FUTURES_FEE_AUTHORITY_RECEIPT_V0.1.json = MEXC_API_FUTURES_FEE_AUTHORITY_PASS
- PROTECTED_2025_SOURCE_AUTHORITY_PASS

If the final 2025 source authority is not PASS, this workflow must not open any 2025 market payload.

## Price source
Use the already-authorized direct reference market:
Binance Spot SOLUSDT 1-minute daily public archives from data.binance.vision.

For each required day:
- download ZIP and companion CHECKSUM;
- SHA256 must match before decompression;
- timestamps must be exact UTC minute boundaries;
- no duplicate, non-monotonic or out-of-day timestamp is allowed;
- missing archive/bar is missingness and is adjudicated by the frozen 95% coverage gate;
- integrity conflict is SOURCE_BLOCKED.

Archive/REST reconciliation:
- select up to 5 acquired timestamps by ascending SHA256 of:
  SOLUSDT || 2025 || timestamp_ms || DLS_RECON_V0.1
- query Binance public Spot 1m kline route for exactly that minute;
- archive OPEN and REST OPEN must be Decimal-identical.

## Signal timing
For each frozen source cluster:
E = first exact UTC minute boundary strictly after T0.
X = E + 5 minutes.

If X >= 2026-01-01T00:00:00Z, exclude as protected-boundary crossing before market acquisition.

Required bars:
OPEN(E), OPEN(X).

## Coverage
Denominator = all source clusters whose E/X remain wholly inside 2025.
Numerator = denominator clusters with both required OPEN bars.
Required coverage >=95%.

No return is computed until checksum/integrity/reconciliation and coverage gates pass.

## Serialization
Among source+market complete clusters:
- sort by E then cluster_id;
- accept first;
- suppress any later cluster with E < current accepted X;
- E == X is eligible.
No overlap, no pyramiding.

## Returns and costs
Gross short simple return:
(P_entry - P_exit) / P_entry

Primary net:
gross - 0.0026

Hard-stress net:
gross - 0.0040

No leverage.

## Statistical gate
Eligible serialized N >=500.

Primary statistic = mean primary-net return.

Day-block bootstrap:
- block key = UTC date of source T0;
- 5,000 repetitions;
- resample observed day blocks with replacement, preserving all trades in each sampled day;
- pair-weighted mean across sampled blocks;
- PRNG seed = full unsigned SHA256 integer of the exact UTF-8 string:
  DEFI-LIQUIDATION-SHOCK-0012025-economic-holdout5mV0.1
- 95% CI = type-7 linear interpolation, identical to canonical Discovery/OOS implementation.

Inferential protocol family set is fixed from canonical OOS:
kamino, marginfi, save11.

SURVIVES_2025_ECONOMIC_HOLDOUT iff:
- serialized N >=500;
- source/market coverage >=95%;
- mean primary-net >0;
- bootstrap 95% lower bound primary-net >0;
- at least 2 of {kamino,marginfi,save11} have positive mean primary-net.

Otherwise, with valid source/market data:
NO_EDGE_2025_ECONOMIC_HOLDOUT.

Source/integrity/coverage failure:
SOURCE_BLOCKED_2025_ECONOMIC_HOLDOUT.

The 40 bps hard-stress result is supportive only and cannot rescue or kill the primary classification.

## Firewall
protected_2025_market_outcomes_opened=false
protected_2026_outcomes_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
