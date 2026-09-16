# DEFI-LIQUIDATION-SHOCK-001 — HISTORICAL DECODER AUTHORITY MATRIX V0.1

Status: SOURCE-GATE / OUTCOME-BLIND  
Frozen event window: 2021-01-01 through 2024-12-31 UTC  
No prices, returns, PnL or direction tests are authorized by this document.

## Rule

A current SDK/IDL is not automatically historical authority. Candidate events may be enumerated with reference discriminators, but they become authoritative liquidation events only after the relevant historical program/IDL interval is pinned or independently reconciled against equivalent historical source evidence.

## Save / Solend

Program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

### Native tag `0x0c` — `LiquidateObligation`

Strong historical evidence exists:

- archived `solendprotocol/solend-sdk` initial instruction-enum commit `c93fbc81fcc68610ad64fbce4a170a38335b7d7f`, dated 2021-12-08, already assigns `LiquidateObligation = 12`;
- the archived SDK final state in October 2022 still assigns tag 12;
- the migrated `solendprotocol/public` SDK in October 2022 retains tag 12;
- sampled 2023 and 2024 SDK states retain tag 12.

Current classification: `HISTORICALLY_SUPPORTED_FROM_2021-12-08_SOURCE_COMMIT`, subject to chain-deployment activation and any candidate event predating that source commit.

### Native tag `0x11` — `LiquidateObligationAndRedeemReserveCollateral`

The chronology is materially different:

- absent from the archived SDK enum on 2021-12-08;
- absent from the migrated SDK on 2022-10-13;
- absent from sampled SDK states on 2023-05-29 and 2024-05-28;
- present in the SDK enum by commit `91d2936930b412ce752be71c6d166deba65489cc` dated 2024-07-19;
- a dedicated instruction-builder file has commit history beginning no later than 2024-08-06.

Therefore tag `0x11` MUST NOT be back-applied to 2021-2023 or early 2024. Exact on-chain activation/deployment boundary remains to be proven before any `0x11` candidate is counted as an authoritative event.

## marginfi v2

Program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`

Reference discriminator:

- `lending_account_liquidate`
- Anchor 8-byte prefix `d6a997d5fba756db`

Current repository/IDL evidence confirms the instruction and the mainnet program ID, but the exact version intervals covering 2023-2024 are not yet frozen here. Later 2026-era start/end liquidation flows must not be back-applied.

Current classification: `REFERENCE_ONLY_PENDING_HISTORICAL_VERSION_MAP`.

## Kamino Lend

Program: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

Reference discriminator:

- `liquidateObligationAndRedeemReserveCollateral`
- Anchor 8-byte prefix `b1479acce2854a37`

Historical public-repository boundary now pinned outcome-blind:

- the official `Kamino-Finance/klend-sdk` repository returns no commits at or before 2024-08-31 in the currently available public history;
- the earliest public commit found in the repository history is `fdffe6b6115e254020af2bb52fa1ed8e3b73f438`, dated 2024-09-26;
- that commit contains `src/idl_codegen/instructions/liquidateObligationAndRedeemReserveCollateral.ts`;
- the instruction builder in that commit encodes identifier bytes `[177, 71, 154, 188, 226, 133, 74, 55]`, i.e. hex `b1479acce2854a37`, matching the pre-registered reference discriminator.

This establishes public-source decoder evidence no later than 2024-09-26. It does NOT prove that the same instruction/version was active on-chain before that date, and it provides no authority to back-apply the current decoder to 2023 or 2024-01-01 through 2024-09-25. Earlier intervals remain fail-closed until independently pinned from historical source or chain evidence.

Current classification: `PUBLIC_REPO_DECODER_SUPPORTED_FROM_2024-09-26; EARLIER_INTERVAL_PENDING_HISTORICAL_VERSION_MAP`.

## Drift V2

Program: `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`

Reference liquidation family currently enumerated:

- `liquidate_perp` — `4b2377f7bf128b02`
- `liquidate_spot` — `6b00802923e5fb12`
- `liquidate_borrow_for_perp_pnl` — `a911205acf94d11b`
- `liquidate_perp_pnl_for_deposit` — `ed4bc6ebe9ba4b23`
- `liquidate_spot_with_swap_begin` — `0c2bb0539cfb750d`
- `liquidate_spot_with_swap_end` — `8e58a3a0df4b37e1`

The Anchor discriminators are deterministic from `global:<instruction_name>`, and public Drift IDL evidence confirms these liquidation-family names in modern code. Historical existence/completeness across 2021-2024 remains to be mapped. Bankruptcy instructions/events are intentionally separate and are not silently included.

Current classification: `REFERENCE_ONLY_PENDING_HISTORICAL_VERSION_MAP`.

## Consequence for the source census

BigQuery may be used to find all reference-discriminator candidates in the frozen window. Helius archival RPC may be used to reconcile raw transaction bytes and CPI position. Neither step, by itself, upgrades a `REFERENCE_ONLY` interval to historical decoder authority.

The authority upgrade is protocol/interval-specific and must be documented before `SOURCE_DATA_PASS`.
