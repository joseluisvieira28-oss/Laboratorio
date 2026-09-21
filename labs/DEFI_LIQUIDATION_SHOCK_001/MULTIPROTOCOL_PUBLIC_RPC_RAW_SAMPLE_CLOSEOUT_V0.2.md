# DEFI-LIQUIDATION-SHOCK-001 — MULTIPROTOCOL PUBLIC RPC RAW SAMPLE CLOSEOUT V0.2

Date: 2026-09-21  
Status: **SOURCE-ONLY RAW SAMPLE VERIFICATION COMPLETE / GLOBAL SOURCE_DATA_PASS=false**

## Input

All 23 rows from the pre-existing frozen `DLS_RAW_VALIDATION_SAMPLE_V01.csv` were executed. No post-result row selection was permitted.

Frozen candidate-set blob:
`efc571f7282d99a626edebd3a26676406aba7f4f`

## Execution

GitHub Actions run: `35648898381`  
Job: `106496073382`  
Head commit: `05d9ca71a186c2dcabca164f8709cdc5338e5610`  
Endpoint: official public Solana mainnet RPC  
Method: `getTransaction` / `jsonParsed`

## Aggregate result

- rows executed: **23 / 23**
- structurally RAW-valid rows: **23 / 23**
- successful realized liquidation references: **14**
- RAW-verified failed attempts: **9**
- transport blocked: **0**
- content mismatches: **0**

## Class adjudication

### REALIZED_SUCCESS_CONFIRMED_BY_2024_12_15
- Drift v2 / `liquidate_perp`: 2 success, 4 failed attempts, 6 structural-valid
- Drift v2 / `liquidate_perp_pnl_for_deposit`: 1 success, 2 failed attempts, 3 structural-valid
- Drift v2 / `liquidate_spot`: 6 success, 0 failed attempts, 6 structural-valid
- marginfi v2 / `lending_account_liquidate`: 3 success, 0 failed attempts, 3 structural-valid
- Save/Solend / `LiquidateObligationAndRedeemReserveCollateral (0x11)`: 2 success, 2 failed attempts, 4 structural-valid

### DECODER_CONFIRMED_SUCCESS_NOT_ESTABLISHED
- Drift v2 / `liquidate_borrow_for_perp_pnl`: 0 success, 1 RAW-verified failed attempt

### NOT TESTED BY THIS SAMPLE
- Save/Solend / legacy `LiquidateObligation (0x0c)` — absent from the pre-existing sample.

No class receives earliest-boundary credit from this run.

## Evidence

GitHub artifact:
- ID: `10661212057`
- SHA256: `d8df4dce6a50a677ee2ae917aee9286a7b0d78e4a73deeb42d33f8c498a38fb7`
- size: 158,370 bytes

Drive copy:
- `DLS_MULTIPROTOCOL_PUBLIC_RPC_RAWVERIFY_EVIDENCE_V0.2.zip`
- Drive ID: `1sRV0J7tRKCpbXrN_U0stxMNLudxSy2hw`

## Scientific meaning

This materially strengthens source feasibility:
- official public RPC can retrieve and reconcile the historical 2024 transactions;
- the pinned decoders for five represented liquidation classes have successful realized examples;
- the Drift borrow-for-perp-PnL decoder is structurally correct in the sample but realized success remains unproven by that sample;
- legacy Save/Solend 0x0c remains untested here.

This is **not** predictive evidence and is **not** an economic edge result.

## Remaining SOURCE_DATA_PASS blockers

The already-frozen requirements still stand:
- chronological first-success boundaries;
- complete bounded census for authoritative intervals;
- realized event population completeness;
- unresolved-class RAW validation;
- frozen numerical sample gate;
- FINAL PRE-DISCOVERY AUTHORITY.

## Firewall

Prices=false; returns=false; PnL=false; direction=false; market-response outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; merge main=false.
