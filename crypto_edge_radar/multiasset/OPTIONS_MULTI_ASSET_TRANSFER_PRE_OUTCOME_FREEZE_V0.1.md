# OPTIONS MULTI-ASSET TRANSFER — PRE-OUTCOME SCIENCE FREEZE V0.1

Date: 2026-10-02  
Status: FROZEN_PRE_OUTCOME  
Branch: `options-multiasset-fourhook-prep-v0.1-2026-10-02`

## Purpose

Test whether the already-defined OPTIONS-SPOTPERP V2.1 mechanism transfers, without tuning, from BTC to three new independent hooks:

- OPTIONS-ETH-001-V0.1
- OPTIONS-SOL-001-V0.1
- OPTIONS-XRP-001-V0.1

Each asset is adjudicated independently. No asset may rescue, promote, or veto another.

## Frozen signal identity

For each asset and UTC signal date t:

- source: Deribit historical option trades;
- ETH request currency: ETH, instrument prefix `ETH-`;
- SOL request currency: USDC, instrument prefix `SOL_USDC-`;
- XRP request currency: USDC, instrument prefix `XRP_USDC-`;
- historical XRP strike token `d` is the already-proven decimal marker and is normalized before numeric parsing;
- DTE: 30 to 120 calendar days inclusive;
- calls: strike / index price in [1.05, 1.20];
- puts: strike / index price in [0.80, 0.95];
- reject missing, non-finite or non-positive IV/index values;
- require at least 5 distinct eligible call instruments and 5 distinct eligible put instruments on the day;
- per instrument/day IV = median transaction IV;
- call side IV = median eligible call-instrument daily IV;
- put side IV = median eligible put-instrument daily IV;
- signal = CALL_IV - PUT_IV;
- positive signal = LONG;
- negative signal = SHORT;
- zero signal = FLAT.

No threshold sweep, alternate DTE band, alternate moneyness band, alternate aggregation, direction reversal, subgroup rescue or asset cross-subsidy is authorized.

## Frozen scientific outcome

For each asset:
- outcome price series: matching Binance Spot `ASSETUSDT` daily klines;
- entry: 00:00 UTC open on t+1;
- exit: 00:00 UTC open on t+2;
- return: log(exit_open / entry_open);
- aligned gross return = direction * forward log return.

The scientific outcome remains spot-based to preserve the V2.1 research identity. Any later MEXC futures route is an execution translation and must not rewrite this scientific result.

## Frozen causal V2.1 risk scaling

Price-history start for all three transfer experiments: 2023-01-01 UTC.

- risk input: matching ASSETUSDT close-to-close daily log returns available through t only;
- RV window: 20 valid daily log returns;
- baseline: expanding median of all valid RV20 observations from the frozen price-history start through t;
- minimum valid RV20 history: 60;
- weight = min(1.0, expanding_median_RV20_t / RV20_t);
- maximum weight = 1.0;
- no leverage above 1x in the scientific model;
- no additional filter or floor.

## Costs

- BASE: 10 bps at full notional, scaled linearly by executed weight.
- STRESS: 20 bps at full notional, scaled linearly by executed weight.

STRESS20 is a mandatory fragility diagnostic and is not by itself a veto if BASE10 hard gates pass.

## Development window

Outcome-bearing Development signal dates are calendar 2024 only.

Source availability:
- ETH: 2024-01-01 through 2024-12-31.
- SOL: source census begins with listing-era data in March 2024.
- XRP: source census begins with listing-era data in March 2024.

A 2024 signal is evaluable only if both t+1 and t+2 opens are inside calendar 2024. No 2025 price may be used to resolve a 2024 Development signal.

### Development hard gates

All must pass for that asset to unlock its one-shot 2025 OOS:

A. Provenance/source/leakage gate PASS.  
B. Entered scaled trades N >= 100.  
C. Average executed notional >= 0.40.  
D. BASE10 net mean > 0 bps/opportunity.  
E. BASE10 profit factor > 1.00.  
F. BASE10 cumulative net return > 0.  
G. At least 3 calendar quarters contain >=10 entered trades, and at least 2 such qualifying quarters have non-negative BASE10 mean.  
H. No single calendar quarter contributes >60% of total positive gross PnL.  
I. Exact frozen signal/direction/horizon/cost/risk-scaling identity unchanged.

Development decision:
- all A-I pass => `DEV_SURVIVES__OOS_2025_UNLOCKED`;
- source/provenance failure => `DEV_BLOCKED_SOURCE_PROVENANCE`;
- otherwise => `DEV_REJECTED_EXACT_TRANSFER__2025_REMAINS_LOCKED`.

A max drawdown worse than -50% is recorded as `HIGH_RISK_FRAGILITY` but is not an extra Development rescue/veto gate.

## Protected 2025 OOS

Calendar 2025 option and outcome data for each asset remain LOCKED until that same asset passes all Development gates above.

If and only if Development passes, exactly one 2025 OOS is authorized under this freeze.

- signal dates: calendar 2025 only;
- entry/exit: unchanged t+1 -> t+2;
- no 2026 data may be used;
- final 2025 signals requiring 2026 data remain unresolved;
- no post-Development or post-OOS parameter change is permitted.

### 2025 OOS hard gates

A. Provenance/source/leakage gate PASS.  
B. Resolved entered scaled trades N >= 50.  
C. Average executed notional >= 0.40.  
D. BASE10 net mean > 0 bps/opportunity.  
E. BASE10 profit factor > 1.00.  
F. BASE10 cumulative net return > 0.  
G. At least 2 of 4 calendar quarters have non-negative BASE10 mean.  
H. No single calendar quarter contributes >60% of total positive gross PnL.  
I. Exact identity unchanged.

OOS decision:
- all A-I pass => `TRANSFER_SURVIVES_2025_OOS__FORWARD_ELIGIBLE`;
- adequate N but D/E/F/G fails => `OOS_REJECTED_EXACT_TRANSFER`;
- N < 50 => `INSUFFICIENT_OOS_SAMPLE`;
- source/provenance failure => `OOS_BLOCKED_SOURCE_PROVENANCE`.

A 2025 max drawdown worse than -50% adds a mandatory `HIGH_RISK_FRAGILITY` flag and blocks micro-live consideration until a separately frozen risk envelope exists.

## Governance

Research only.
No main merge.
No live trading.
No orders.
No exchange mutation.
No wallet action.
No 2026 access.
No post-outcome tuning.
No asset substitution after results.
No lowering gates to save a failed hook.

A surviving OOS hook is only forward-eligible. It is not automatically live-authorized.
