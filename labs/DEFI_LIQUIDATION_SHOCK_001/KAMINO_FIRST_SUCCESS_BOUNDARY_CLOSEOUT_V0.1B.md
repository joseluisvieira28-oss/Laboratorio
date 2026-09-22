# DEFI-LIQUIDATION-SHOCK-001 — KAMINO FIRST-SUCCESS BOUNDARY CLOSEOUT V0.1B

Date: 2026-09-22
Status: COMPLETE / SOURCE-ONLY / RAW-VERIFIED

## Classification

`KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_PASS`

## Frozen source identity

- Program: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
- Instruction: `liquidate_obligation_and_redeem_reserve_collateral`
- Discriminator: `b1479abce2854a37`
- Source-supported lower boundary: `2023-11-17T13:25:35Z`

## Exact first successful on-chain boundary

- UTC: `2023-11-17T14:48:24Z`
- Slot: `230572965`
- Signature: `2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv`
- Instruction location: `outer`
- RAW SHA256: `c45f1538fc8b560c759e0248fe542ae8f8a7d2dad23f57e77a4b4f8dd2d447a9`

The chronological continuation crossed the frozen lower boundary after 3,576 additional pages / 3,576,000 additional signatures. Among the boundary-to-resume slice, 45 successful RAW transactions were inspected before the first exact program/discriminator match.

## Evidence

- parent crawl run: `35689367726`
- cursor extraction run: `35702234721`
- continuation run: `35704794316`
- continuation artifact: `10686881756`
- artifact SHA256: `15097adc6e833edfc99ab11f24c6c4057752b2df7c5de831567bdc6cc01ecf14`
- canonical receipt: `DLS_KAMINO_RPC_FIRST_SUCCESS_RECEIPT_V0.1B.json`

## Scientific consequence

Kamino's historical decoder authority is now upgraded from `ONCHAIN_FIRST_SUCCESS_PENDING` to a RAW-verified first-success boundary at `2023-11-17T14:48:24Z`.

This closes the Kamino first-success sub-gate only. It does NOT grant global `SOURCE_DATA_PASS`, does NOT establish economic edge, and does NOT authorize Discovery market outcomes.

Remaining first-success boundaries:
- Save/Solend 0x0c
- Save/Solend 0x11
- marginfi v2 lending_account_liquidate
- Drift v2 four core liquidation classes

Firewall remained intact: prices=false; returns=false; PnL=false; direction=false; 2025/2026 market outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; main merge=false.
