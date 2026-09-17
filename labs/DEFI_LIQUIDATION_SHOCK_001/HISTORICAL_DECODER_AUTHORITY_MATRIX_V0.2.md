# DEFI-LIQUIDATION-SHOCK-001 — HISTORICAL DECODER AUTHORITY MATRIX V0.2

Date: 2026-09-17  
Status: `SOURCE-GATE / OUTCOME-BLIND`  
Frozen event window: `[2021-01-01, 2025-01-01) UTC`

This supersedes V0.1 for future execution while preserving V0.1 unchanged as audit history.

## Authority rule

A current SDK/IDL is not automatically historical authority. A source-code state can establish that a decoder existed by a date, but an authoritative realized liquidation additionally requires a successful on-chain transaction and protocol/date applicability. BigQuery or Helius evidence does not silently back-apply a decoder before its supported interval.

---

## Save / Solend

Program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

### `0x0c` — `LiquidateObligation`

Retained V0.1 evidence:

- archived Solend SDK source already maps `LiquidateObligation = 12` by 2021-12-08;
- later 2022-2024 sampled SDK states retain tag 12.

Classification:

`SOURCE_DECODER_SUPPORTED_FROM_2021-12-08; ONCHAIN_FIRST_SUCCESS_PENDING`

Candidates before the supported source boundary remain fail-closed until independently proven from older authoritative evidence.

### `0x11` — `LiquidateObligationAndRedeemReserveCollateral`

Boundary is now tighter:

- the official SDK state represented by parent commit `9281eddc055479620e170f4220c2a980fffa0c18`, dated 2024-05-28, has no enum value 17 and jumps from 16 to 19;
- commit `91d2936930b412ce752be71c6d166deba65489cc`, dated 2024-07-19, contains `LiquidateObligationAndRedeemReserveCollateral = 17`.

Classification:

`SOURCE_DECODER_SUPPORTED_BY_2024-07-19; ABSENT_IN_2024-05-28_SOURCE_STATE; ONCHAIN_FIRST_SUCCESS_PENDING`

It MUST NOT be back-applied to 2021-2023 or the unsupported early-2024 interval.

---

## marginfi v2

Program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`

Instruction: `lending_account_liquidate`  
Anchor discriminator: `d6a997d5fba756db`

New historical evidence:

- parent source state `607b55ee884e266e84ee2ffd66c2aceac5933f2b`, dated 2023-02-06, already contains `lending_account_liquidate` but declares an older mainnet program ID (`yyyxaNH...`);
- commit `f6d3d5616e293c9468333571c3ceb90bb2410b00`, dated 2023-02-07, changes the mainnet declaration to the frozen current program ID `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA` while retaining `lending_account_liquidate`;
- the discriminator is deterministic Anchor `sha256("global:lending_account_liquidate")[0:8] = d6a997d5fba756db`.

Classification:

`SOURCE_DECODER_SUPPORTED_FOR_CURRENT_PROGRAM_ID_BY_2023-02-07; ONCHAIN_FIRST_SUCCESS_PENDING`

No candidate for the frozen current program ID may be upgraded before the current-ID source boundary without independent chain/program-deployment evidence.

---

## Kamino Lend

Program: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

Instruction: `liquidate_obligation_and_redeem_reserve_collateral`

### Critical correction

Correct Anchor discriminator:

`b1479abce2854a37`

NOT:

`b1479acce2854a37`

Official SDK commit `fdffe6b6115e254020af2bb52fa1ed8e3b73f438` encodes identifier bytes `[177, 71, 154, 188, 226, 133, 74, 55]`, which are exactly `b1479abce2854a37`.

Historical source boundary is also improved:

- official `Kamino-Finance/klend` initial `Program code v1` commit `57074f4599a36ab0b433a71599b206c73efe1fd7`, dated 2023-11-17, already declares the frozen mainnet program ID and exposes the liquidation instruction name;
- therefore Anchor decoder support exists in public program source by 2023-11-17;
- the 2024-09-26 generated SDK independently confirms the exact discriminator bytes.

Classification:

`SOURCE_DECODER_SUPPORTED_BY_2023-11-17; CORRECTED_DISCRIMINATOR; ONCHAIN_FIRST_SUCCESS_PENDING`

Prior Kamino zero-candidate observations generated with the wrong discriminator are invalidated for Kamino only and require rerun.

---

## Drift v2

Program: `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`

### Four core liquidation instructions

- `liquidate_perp` — `4b2377f7bf128b02`
- `liquidate_spot` — `6b00802923e5fb12`
- `liquidate_borrow_for_perp_pnl` — `a911205acf94d11b`
- `liquidate_perp_pnl_for_deposit` — `ed4bc6ebe9ba4b23`

Historical evidence:

- source state `e1f7cb4477c55c6eb69b6b4ea78a38a469024c8e`, dated 2022-10-28, already contains all four instruction names but declares an older mainnet program ID `dammHkt...`;
- commit `e77518dec79b9ade13680d1d8da1a479aca759b1`, dated 2022-11-04, is explicitly `sdk: update mainnet program id`; its program source declares the frozen current ID and contains all four liquidation instructions;
- each frozen 8-byte prefix matches deterministic Anchor `global:<instruction_name>` hashing.

Classification for these four:

`SOURCE_DECODER_SUPPORTED_FOR_CURRENT_PROGRAM_ID_BY_2022-11-04; ONCHAIN_FIRST_SUCCESS_PENDING`

### Spot-liquidation-with-swap pair

Reference discriminators remain recorded for audit history:

- `liquidate_spot_with_swap_begin` — `0c2bb0539cfb750d`
- `liquidate_spot_with_swap_end` — `8e58a3a0df4b37e1`

However preserved Drift protocol history shows commit `5ca90e71edb9911bbe7f66ec3634304c52a8fd74`, dated 2025-01-08, titled `program: liquidate spot with swap (#1402)`, adding the spot-with-swap liquidation implementation.

The frozen scientific window ends at 2025-01-01 UTC.

Classification:

`OUTSIDE_FROZEN_WINDOW_SOURCE_INTRODUCTION_2025-01-08`

Therefore these two reference discriminators MUST NOT be used to classify authoritative Drift liquidations anywhere in the 2021-2024 frozen window. This is historical-applicability enforcement, not post-outcome tuning.

---

## Remaining chain-authority gate

Source-code decoder mapping is now materially stronger, but exact on-chain activation remains to be pinned for:

1. Save `0x0c`;
2. Save `0x11`;
3. marginfi current program + liquidation discriminator;
4. Kamino current program + corrected liquidation discriminator;
5. Drift current program + each of the four core liquidation classes.

The next source-only task is to find the earliest successful matching on-chain candidate at or after each supported source boundary, then RAW-verify the boundary candidate(s).

No `SOURCE_DATA_PASS` is authorized yet.
