# DEFI-LIQUIDATION-SHOCK-001 — MULTIPROTOCOL PUBLIC RPC RAW SAMPLE VERIFICATION FREEZE V0.2

Date: 2026-09-21  
Status: **FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

## Frozen input

Exact candidate file:
`DLS_MULTIPROTOCOL_RAW_VALIDATION_SAMPLE_V0.2.json`

Git blob SHA:
`efc571f7282d99a626edebd3a26676406aba7f4f`

The file contains **all 23 rows** from the pre-existing `DLS_RAW_VALIDATION_SAMPLE_V01.csv`. No row was selected based on RPC result. No row may be added, dropped or replaced after this freeze.

Classes represented:
- Drift v2 `liquidate_borrow_for_perp_pnl`
- Drift v2 `liquidate_perp` (outer and inner references)
- Drift v2 `liquidate_perp_pnl_for_deposit`
- Drift v2 `liquidate_spot` (outer and inner references)
- marginfi v2 `lending_account_liquidate`
- Save/Solend `LiquidateObligationAndRedeemReserveCollateral / 0x11`

The older Save/Solend `LiquidateObligation / 0x0c` class is **not present in this pre-existing sample** and therefore cannot receive credit from this run.

## Source

Official public Solana mainnet RPC:
`https://api.mainnet-beta.solana.com`

Method:
`getTransaction`

Encoding:
`jsonParsed`

No API key, paid source, wallet, identity submission or account creation.

## Per-row RAW test

For each frozen row:
1. transaction result must be non-null;
2. returned slot must equal the frozen slot;
3. an instruction in the frozen location class (outer/inner) must resolve to the exact frozen program ID;
4. its base58 data must decode to bytes beginning with the frozen discriminator/tag;
5. transaction success is independently recorded as `meta.err == null`.

Structural identity and transaction success are separate facts.

A structurally matching row with `meta.err != null` is a verified failed attempt, not a realized liquidation.

A structurally matching row with `meta.err == null` is:
`RAW_VERIFIED_SUCCESSFUL_LIQUIDATION_REFERENCE`.

## Class routing

For each represented decoder class:
- >=1 structurally valid successful row => `REALIZED_SUCCESS_CONFIRMED_BY_2024_12_15`
- structurally valid rows but no successful row => `DECODER_CONFIRMED_SUCCESS_NOT_ESTABLISHED`
- deterministic program/prefix/location mismatch => `RAW_CONTENT_MISMATCH_FAIL_CLOSED`
- endpoint cannot retrieve required history => `TRANSPORT_BLOCKED`

This run **does not pin an earliest first-success boundary**. Chronological boundary work remains separate.

## Global routing

Even if every represented class has a realized successful reference, `SOURCE_DATA_PASS` remains false. The run only closes RAW sample validation for represented classes.

## Firewall

No prices, returns, PnL, future-direction tests, event-size thresholds, market-response outcomes, live trading, orders, wallets, exchange mutation, paid source or main merge.
