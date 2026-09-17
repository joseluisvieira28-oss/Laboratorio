# DEFI-LIQUIDATION-SHOCK-001 — HISTORICAL AUTHORITY ATTACK RECEIPT V0.1

Date: 2026-09-17  
Branch: `defi-liquidation-shock-v0.1`  
Posture: `SOURCE_ONLY / OUTCOME_BLIND / FAIL_CLOSED`

## Result

The public-source decoder investigation materially advanced the Source Gate and found one critical source-registry defect before any historical census or economic outcome was opened.

### 1. Kamino decoder transcription error — FOUND AND QUARANTINED

Retired wrong prefix:

`b1479acce2854a37`

Correct prefix:

`b1479abce2854a37`

Official generated SDK bytes: `[177, 71, 154, 188, 226, 133, 74, 55]`.

Classification of affected prior Kamino zero-result observations:

`DATA_FAILURE / SOURCE_DECODER_TRANSCRIPTION_ERROR`

They are not NO_EDGE and are not evidence of Kamino liquidation absence.

### 2. Kamino historical source boundary — IMPROVED

Official `Kamino-Finance/klend` `Program code v1` commit:

`57074f4599a36ab0b433a71599b206c73efe1fd7` — 2023-11-17

This source state already contains:

- mainnet program `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`;
- `liquidate_obligation_and_redeem_reserve_collateral`.

Source decoder support therefore exists by 2023-11-17. Exact on-chain first successful matching candidate remains pending.

### 3. marginfi v2 historical source boundary — IMPROVED

Parent state on 2023-02-06 contains the liquidation instruction under an older mainnet program ID.

Commit:

`f6d3d5616e293c9468333571c3ceb90bb2410b00` — 2023-02-07

updates the mainnet program to the frozen current ID while retaining `lending_account_liquidate`.

Frozen discriminator `d6a997d5fba756db` matches deterministic Anchor derivation.

Classification:

`SOURCE_DECODER_SUPPORTED_FOR_CURRENT_PROGRAM_ID_BY_2023-02-07; ONCHAIN_FIRST_SUCCESS_PENDING`

### 4. Drift v2 four core liquidation decoders — IMPROVED

A 2022-10-28 source state contains all four core liquidation instruction names under the prior mainnet program ID.

Commit:

`e77518dec79b9ade13680d1d8da1a479aca759b1` — 2022-11-04

updates to the frozen current mainnet ID and retains:

- `liquidate_perp`;
- `liquidate_spot`;
- `liquidate_borrow_for_perp_pnl`;
- `liquidate_perp_pnl_for_deposit`.

All four frozen discriminators match deterministic Anchor derivation.

Classification:

`SOURCE_DECODER_SUPPORTED_FOR_CURRENT_PROGRAM_ID_BY_2022-11-04; ONCHAIN_FIRST_SUCCESS_PENDING`

### 5. Drift spot-liquidation-with-swap — OUTSIDE FROZEN WINDOW

Preserved protocol history commit:

`5ca90e71edb9911bbe7f66ec3634304c52a8fd74` — 2025-01-08

is explicitly titled `program: liquidate spot with swap (#1402)` and adds the implementation.

The frozen lab window ends before 2025-01-01.

Therefore `liquidate_spot_with_swap_begin` and `liquidate_spot_with_swap_end` remain recorded reference discriminators but are not historically applicable to the 2021-2024 authoritative population.

### 6. Save 0x11 boundary — TIGHTENED

Official SDK state dated 2024-05-28 lacks enum value 17.

Commit:

`91d2936930b412ce752be71c6d166deba65489cc` — 2024-07-19

contains:

`LiquidateObligationAndRedeemReserveCollateral = 17`

Classification:

`SOURCE_DECODER_SUPPORTED_BY_2024-07-19; ONCHAIN_FIRST_SUCCESS_PENDING`

### 7. Save 0x0c — RETAINED

Archived SDK commit `c93fbc81fcc68610ad64fbce4a170a38335b7d7f`, dated 2021-12-08, already has:

`LiquidateObligation = 12`

Classification remains:

`SOURCE_DECODER_SUPPORTED_FROM_2021-12-08; ONCHAIN_FIRST_SUCCESS_PENDING`

## New execution assets

- `SOURCE_DECODER_CORRECTION_KAMINO_V0.1.md`
- `HISTORICAL_DECODER_AUTHORITY_MATRIX_V0.2.md`
- `source/BIGQUERY_BOUNDED_CANDIDATE_CENSUS_V0_3.sql`
- `source/BIGQUERY_KAMINO_CORRECTED_SMOKE_TEST_V0_1.sql`
- `source/BIGQUERY_ANCHOR_LIQUIDATION_LOG_LOCATOR_V0_1.sql`

## Exact next gate

Before any broad historical census, execute the corrected 2024-12-15 Kamino smoke test.

Required file:

`source/BIGQUERY_KAMINO_CORRECTED_SMOKE_TEST_V0_1.sql`

Rules:

1. dry-run / inspect estimated bytes first;
2. if estimate >100 GB: STOP;
3. otherwise execute;
4. export every returned row to CSV;
5. if successful candidates exist, build a deterministic corrected Kamino RAW validation sample;
6. if zero candidates remain, do NOT infer absence — move to source-only historical locator chunks using the corrected decoder.

## Current verdict

`SOURCE GATE ACTIVE`

- Transaction execution-state semantics: PASS.
- Historical public-source decoder map: materially advanced.
- Kamino decoder registry: corrected, revalidation pending.
- Exact on-chain first-success boundaries: pending.
- Historical candidate census: not yet authorized as complete.
- `SOURCE_DATA_PASS`: NOT YET.

No economic outcome was opened.
