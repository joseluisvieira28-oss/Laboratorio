# IMPORTED-FROZEN-SIGNAL-FWD-001 — ELIGIBILITY AUDIT FREEZE V0.13.1

Date: 2026-10-03
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED
Parent: V0.13 Event-Conditioned Edge freeze.

## Purpose

Audit pre-existing Crypto Lab candidates for exact, non-rescued transfer into the V0.13
Event Futures shadow protocol.

This audit opens ZERO Event Futures outcomes. It does not rank candidates by later
performance and it does not modify any parent scientific rule.

## Hard eligibility criteria

A candidate is import-eligible only if ALL are true:

1. its scientific rule and prospective authority were frozen before V0.13;
2. its direction can be mapped exactly to Event Futures UP/DOWN without inversion;
3. its tested holding horizon maps exactly to an available Event Futures cycle;
4. its underlying market maps exactly to an available Event Futures product without
   pair, asset, timeframe or execution substitution;
5. the signal can be emitted prospectively from public/read-only evidence with a
   timestamp known before the Event Futures decision snapshot;
6. no prior frozen Event Futures transfer of the same economic signal/horizon was
   already closed as NO_SURVIVOR, because V0.13 may not be used as a rescue rerun;
7. no parent freeze explicitly forbids the mapping required for import.

Missing evidence => BLOCKED / NOT_ELIGIBLE. Never infer compatibility.

## Frozen candidate whitelist

Only these pre-existing candidates are audited in this version:

- ETF-CME-INSTFLOW-001
- OPTIONS-SPOTPERP-001-V2.1
- HTF-DH03-12H-STANDALONE-FORWARD-V1
- TFG-DONCHIAN-1D-FORWARD-SHADOW-V0.1
- TFG-DONCHIAN-REGIME-ADAPTATION-V1-FORWARD
- BNB-LAUNCHPOOL-DEMAND-001
- CED1D-0031

No candidate may be added after this audit sees a current product snapshot.
A new candidate requires a new audit version and future boundary.

## Candidate authority anchors

### OPTIONS-SPOTPERP-001-V2.1
Authority:
`options-spotperp-v21-live-shadow-v0.1@c8822a72a1f844e378d170a819738ba0cd8bd1b6`
`crypto_edge_radar/OPTIONS_SPOTPERP_001_V21_LIVE_SHADOW_FREEZE_V0.1.json`

Frozen identity includes:
- signal CALL_IV_MINUS_PUT_IV;
- positive LONG / negative SHORT;
- BTCUSDT;
- 00:00 UTC t+1 to 00:00 UTC t+2, exactly 24h.

Prior Event Futures transfer:
run 37043309948, verdict `NO_SURVIVOR_AT_FROZEN_V11_GATE`.
Therefore this exact signal family is CLOSED for V0.13 rescue import.

### ETF-CME-INSTFLOW-001
Prior Event Futures transfer authority:
`mexc-event-futures-etfcme-transfer-v1.0.2-min30-2026-10-02@979c4c84653b293fae2d4b513117ab44473c0e02`
`research/mexc_event_futures/ETF_CME_MIN30_TRANSFER_FREEZE_V1.0.2.md`

Frozen parent direction:
positive CFTC institutional-flow signal => UP; negative => DOWN.
Prior Event Futures transfer run 37042519225:
`NO_SURVIVOR_AT_FROZEN_V102_GATE`.
Therefore the same signal/horizons are CLOSED for V0.13 rescue import.

### HTF-DH03-12H-STANDALONE-FORWARD-V1
Authority:
`htf-dh03-12h-standalone-forward-v0.1@402e731271e40d49ad275b73247f5839aa5f22af`
`crypto_edge_radar/HTF_DH03_12H_STANDALONE_FORWARD_V1_FREEZE.json`

Frozen rule:
12H UTC LONG-only Donchian signal, entry next 12H open, stop/target and maximum 80
12H bars. Parent explicitly forbids timeframe substitution.

A fixed Event Futures binary horizon is not identical to this variable stop/target
execution path. Do not substitute 12h, 1d or any other binary expiry.

### TFG-DONCHIAN-1D-FORWARD-SHADOW-V0.1
Authority:
`tfg-donchian-1d-oos-2025-v01@3364c2fdd80b100579c31522501c25de553813f2`
`Dream-Account-OS-v2.3-PARTIAL/research/timeframe_gap/TFG_DONCHIAN_1D_FORWARD_SHADOW_V0.1_FREEZE.json`

Frozen rule:
daily breakout, next daily open, stop/target, max 40 daily bars.
A 1-day binary Event Futures expiry would replace the frozen exit logic and is not
an exact import.

### TFG-DONCHIAN-REGIME-ADAPTATION-V1-FORWARD
Same authority branch.
Frozen rule:
12H LONG-only with stop/target and max 80 bars; no timeframe substitution.
Not an exact binary-horizon import.

### BNB-LAUNCHPOOL-DEMAND-001
Authority:
`bnb-launchpool-demand-forward-shadow-v01@efd676a8e2c3b11f720f4fdf3f476e9a00d281db`
`Dream-Account-OS-v2.3-PARTIAL/research/bnb_launchpool_demand_001/BNB_LAUNCHPOOL_DEMAND_001_FORWARD_SHADOW_V0.1_FREEZE.json`

Frozen execution:
LONG BNBBTC spot, first eligible 15m open, exactly 24h hold.
An Event Futures BNB_USDT or BTC_USDT product would be a pair/underlying substitution.
Only an exact BNBBTC Event Futures product could satisfy this audit.

### CED1D-0031
Authority:
`ced1d-runtime-reconciliation-2026-09-30@60aef0ff562b4a236d68afea5408908c361fa7ea`
`crypto_edge_radar/authorities/CED1D_0031_RENDER_SHADOW_ACTIVATION_V0.3.json`

Frozen identity:
AVAXUSDT, continuation, horizon 1 day.
This is potentially structurally mappable only if an exact AVAX_USDT Event Futures
product with a 1-day cycle is present in the fresh product snapshot. No substitute asset.

## Fresh exact-product gate

Before final audit verdict, obtain a NEW unauthenticated passive Event Futures product
snapshot using the already frozen V0.12 browser collector.

No active private `detail` call, login, account read, order or mutation.

The snapshot is used ONLY to establish present product/cycle availability.
It opens no candidate signal and no outcome.

## Audit verdicts

Per candidate:
- `ELIGIBLE_FOR_SEPARATE_IMPORT_ACTIVATION_FREEZE`
- `CLOSED_PRIOR_EVENT_FUTURES_NO_SURVIVOR`
- `NOT_ELIGIBLE_HORIZON_OR_EXECUTION_SUBSTITUTION`
- `NOT_ELIGIBLE_PRODUCT_OR_PAIR_MISMATCH`
- `BLOCKED_MISSING_AUTHORITY`

Global:
- `IMPORT_ELIGIBLE_CANDIDATES_PRESENT`
- `NO_ELIGIBLE_IMPORTS_AT_FROZEN_AUDIT`

No import family becomes ACTIVE from this audit alone.
