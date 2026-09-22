# DEFI-LIQUIDATION-SHOCK-001 — HISTORICAL DECODER AUTHORITY MATRIX V0.3

Date: 2026-09-22  
Status: `SOURCE-GATE / OUTCOME-BLIND / PARTIALLY CLOSED`  
Frozen event window: `[2021-01-01, 2025-01-01) UTC`

This supersedes V0.2 for current source-gate state while preserving V0.1/V0.2 unchanged as audit history.

## Authority rule

A current SDK/IDL is not automatically historical authority. A source-code state establishes decoder applicability only from its supported historical interval. A realized liquidation additionally requires a successful on-chain transaction, exact program/instruction identity and RAW reconciliation. No decoder is silently back-applied before its supported interval.

---

## Save / Solend

Program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

### `0x0c` — `LiquidateObligation`

Source authority retained:
- archived Solend SDK source maps `LiquidateObligation = 12` by 2021-12-08;
- later sampled SDK states retain tag 12.

Current classification:

`SOURCE_DECODER_SUPPORTED_FROM_2021-12-08; ONCHAIN_FIRST_SUCCESS_PENDING`

Current transport state:
- V0.1 crawl: 5,000,000 signatures, page-cap blocked;
- V0.2 continuation: additional 5,000,000 signatures, page-cap blocked;
- deterministic V0.3 resume cursor: slot `175932243`, time `2023-02-04T05:28:20Z`;
- V0.3 continuation run: `35771022352`.

No scientific failure has occurred. Page-cap blockers are operational only.

### `0x11` — `LiquidateObligationAndRedeemReserveCollateral`

Historical source authority retained:
- absent in official SDK source state dated 2024-05-28;
- supported by official SDK commit `91d2936930b412ce752be71c6d166deba65489cc`, dated 2024-07-19.

RAW-verified first-success boundary:

- classification: `SAVE11_FIRST_SUCCESS_BOUNDARY_RPC_PASS`
- UTC: `2024-07-19T19:30:52Z`
- slot: `278496102`
- signature: `WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L`
- instruction location: `inner`
- RAW SHA256: `fcb3ae8029b3a5f69c29c8580fe3630a6b29e7246d0a98561d522e582514203c`
- workflow run: `35715830047`
- artifact: `10690805384`
- artifact SHA256: `e72c22a7164ba8787c03201a3d7b2eb1a42a6ffc4384d3dcb8e80695aa9e8c7c`

Current classification:

`SOURCE_DECODER_SUPPORTED_BY_2024-07-19; ABSENT_IN_2024-05-28_SOURCE_STATE; RAW_VERIFIED_FIRST_SUCCESS_2024-07-19T19:30:52Z`

It MUST NOT be back-applied before the supported source interval.

---

## marginfi v2

Program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`

Instruction: `lending_account_liquidate`  
Anchor discriminator: `d6a997d5fba756db`

Historical source authority retained:
- parent source state dated 2023-02-06 contains the instruction but an older mainnet program ID;
- commit `f6d3d5616e293c9468333571c3ceb90bb2410b00`, dated 2023-02-07, switches to the frozen current program ID while retaining the instruction;
- discriminator equals deterministic Anchor `sha256("global:lending_account_liquidate")[0:8]`.

Current classification:

`SOURCE_DECODER_SUPPORTED_FOR_CURRENT_PROGRAM_ID_BY_2023-02-07; ONCHAIN_FIRST_SUCCESS_PENDING`

Current transport state:
- V0.1: 5,000,000 signatures, page-cap blocked;
- V0.2: additional 5,000,000 signatures, page-cap blocked;
- deterministic V0.3 resume cursor: slot `239637875`, time `2024-01-03T12:26:07Z`;
- V0.3 continuation run: `35771014450`.

No candidate before the frozen current-program source boundary may be upgraded without independent chain/program authority.

---

## Kamino Lend

Program: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

Instruction: `liquidate_obligation_and_redeem_reserve_collateral`  
Correct discriminator: `b1479abce2854a37`

Historical source authority retained:
- official `Kamino-Finance/klend` initial Program code v1 commit `57074f4599a36ab0b433a71599b206c73efe1fd7`, dated 2023-11-17, already declares the frozen mainnet program ID and liquidation instruction;
- generated SDK evidence independently confirms exact discriminator bytes;
- retired wrong discriminator `b1479acce2854a37` remains forbidden.

RAW-verified first-success boundary:

- classification: `KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_PASS`
- UTC: `2023-11-17T14:48:24Z`
- slot: `230572965`
- signature: `2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv`
- instruction location: `outer`
- RAW SHA256: `c45f1538fc8b560c759e0248fe542ae8f8a7d2dad23f57e77a4b4f8dd2d447a9`
- workflow run: `35704794316`
- artifact: `10686881756`
- artifact SHA256: `15097adc6e833edfc99ab11f24c6c4057752b2df7c5de831567bdc6cc01ecf14`

Current classification:

`SOURCE_DECODER_SUPPORTED_BY_2023-11-17; CORRECTED_DISCRIMINATOR; RAW_VERIFIED_FIRST_SUCCESS_2023-11-17T14:48:24Z`

---

## Drift v2

Program: `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`

Four core classes, all source-supported for the frozen current program ID from 2022-11-04T15:17:54Z:

- `liquidate_perp` — `4b2377f7bf128b02`
- `liquidate_spot` — `6b00802923e5fb12`
- `liquidate_borrow_for_perp_pnl` — `a911205acf94d11b`
- `liquidate_perp_pnl_for_deposit` — `ed4bc6ebe9ba4b23`

Historical source authority retained:
- 2022-10-28 source already contains all four names but declares older mainnet program ID `dammHkt...`;
- commit `e77518dec79b9ade13680d1d8da1a479aca759b1`, dated 2022-11-04, updates mainnet program ID to the frozen current ID and retains all four instructions;
- discriminators match deterministic Anchor `global:<instruction_name>`.

Current classification for all four:

`SOURCE_DECODER_SUPPORTED_FOR_CURRENT_PROGRAM_ID_BY_2022-11-04; ONCHAIN_FIRST_SUCCESS_PENDING`

Current source-route state:
- historical S3 documentation establishes that flat-file liquidations are USER-scoped:
  `user/{accountKey}/liquidationRecords/{year}/{YYYYMMDD}`;
- prior MARKET-scoped `liquidationRecords` probes are technically invalid for route-existence adjudication;
- GET-status-only S3 transport calibration run is active on branch `dls-drift-historical-s3-get-control-v0.3`;
- independent early-chain upper-anchor probe is active as run `35771953067`, targeting 2022-12-01 to bound the first ~27 days after decoder activation.

### Spot-liquidation-with-swap pair

- `liquidate_spot_with_swap_begin` — `0c2bb0539cfb750d`
- `liquidate_spot_with_swap_end` — `8e58a3a0df4b37e1`

Preserved source history introduces this pair on 2025-01-08, after the frozen scientific window.

Classification:

`OUTSIDE_FROZEN_WINDOW_SOURCE_INTRODUCTION_2025-01-08`

They MUST NOT be used in the frozen 2021-2024 event population.

---

## Chain-authority gate status

Closed:
1. Save `0x11` — RAW-verified first success.
2. Kamino corrected discriminator — RAW-verified first success.

Pending:
1. Save `0x0c`.
2. marginfi v2 current program.
3. Drift v2 four core classes.

No `SOURCE_DATA_PASS` is authorized yet.

No prices, returns, PnL, future direction, event-size threshold tuning, protocol winner selection, live trading, orders, wallets, exchange mutation or merge to main are authorized by this matrix.
