# DEFI-LIQUIDATION-SHOCK-001 — DRIFT SQD SINGLE-D8 CALIBRATION FREEZE V0.1

Date: 2026-09-25
Status: FROZEN SOURCE-ONLY CALIBRATION / OUTCOME-BLIND

## Purpose

Calibrate whether a single SQD `d8` discriminator filter is exactly equivalent to programId-only enumeration followed by local Base58 discriminator decoding for one Drift instruction class.

This calibration is transport/source only. It does not alter any scientific identity, event window, source population, success semantics, or economic test.

## Calibration slice

Exact UTC slice:
`[2022-11-07T00:00:00Z, 2022-11-08T00:00:00Z)`

Program:
`dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`

Reference programId-only enumeration from the already-complete first Drift partition observed all three classes below in this slice.

Calibrate independently:
- `liquidate_perp` — `4b2377f7bf128b02`
- `liquidate_spot` — `6b00802923e5fb12`
- `liquidate_perp_pnl_for_deposit` — `ed4bc6ebe9ba4b23`

The unresolved class `liquidate_borrow_for_perp_pnl` / `a911205acf94d11b` is NOT used to decide calibration success.

## Exact-equivalence rule

For the same slice and transport envelope:
1. enumerate exact Drift instructions using programId-only query + local Base58 decode;
2. independently query SQD with exact programId + one exact `d8` filter per class;
3. locally decode every d8-returned instruction again;
4. compare exact identity sets:
   `class + signature + instructionAddress + slot + timestamp`;
5. compare execution classifications for every key;
6. require zero extras, zero missing keys, zero conflicting classifications, and zero source anomalies for all three calibration classes.

PASS:
`DRIFT_SQD_SINGLE_D8_EXACT_EQUIVALENCE_PASS`

Any mismatch:
`DRIFT_SQD_SINGLE_D8_CALIBRATION_FAIL_CLOSED`

## Authorized follow-on after PASS

Only after PASS, a separate source-only locator may use exact programId + single d8 `a911205acf94d11b` to search for the earliest successful `liquidate_borrow_for_perp_pnl` candidate.

That locator:
- is not a census substitute;
- cannot create GLOBAL SOURCE PASS;
- cannot alter earlier programId-only evidence;
- requires official Solana RPC RAW verification before boundary PASS;
- must adjudicate chronology against complete earlier source partitions.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
