# DEFI-LIQUIDATION-SHOCK-001 — KAMINO + SAVE11 FIELD ENRICHMENT IMPLEMENTATION FREEZE V0.6

Date: 2026-09-23
Status: FROZEN BEFORE CENSUS OUTCOME / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

This phase may execute only after:
1. `SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE`; and
2. `RAW_SAMPLE_RECONCILIATION_PASS`.

It is subordinate to:
- `KAMINO_SAVE11_HISTORICAL_FIELD_AUTHORITY_FREEZE_V0.1.md`;
- `KAMINO_SAVE11_SQD_EVENT_CENSUS_EXECUTOR_FREEZE_V0.4.2.md`;
- `KAMINO_SAVE11_RAW_SAMPLE_RECONCILIATION_FREEZE_V0.5.md`.

## Purpose

Reconstruct source-level causal fields for every exact Kamino V1 / Save11 census instruction without opening market outcomes.

The enrichment re-queries the same frozen SQD day/slot chunks and requests instruction `accounts` in addition to the already-used source fields.

It MUST join one-to-one against the frozen census instruction key:
`protocol + signature + instructionAddress`.

No new event may be introduced by enrichment.

## Kamino V1

Exact discriminator:
`b1479abce2854a37`.

Instruction bytes:
- first 8 bytes discriminator;
- next three little-endian u64 values.

### 16-account layout

Recognized only when exact account count == 16.

Fields:
0 liquidator
1 obligation
2 lending_market
3 lending_market_authority
4 repay_reserve
5 repay_reserve_liquidity_supply
6 withdraw_reserve
7 withdraw_reserve_collateral_mint
8 withdraw_reserve_collateral_supply
9 withdraw_reserve_liquidity_supply
10 withdraw_reserve_liquidity_fee_receiver
11 user_source_liquidity
12 user_destination_collateral
13 user_destination_liquidity
14 token_program
15 instruction_sysvar_account

Args:
- liquidity_amount_native
- min_acceptable_received_collateral_amount_native
- max_allowed_ltv_override_percent_raw

### 20-account layout

Recognized only when exact account count == 20.

Fields:
0 liquidator
1 obligation
2 lending_market
3 lending_market_authority
4 repay_reserve
5 repay_reserve_liquidity_mint
6 repay_reserve_liquidity_supply
7 withdraw_reserve
8 withdraw_reserve_liquidity_mint
9 withdraw_reserve_collateral_mint
10 withdraw_reserve_collateral_supply
11 withdraw_reserve_liquidity_supply
12 withdraw_reserve_liquidity_fee_receiver
13 user_source_liquidity
14 user_destination_collateral
15 user_destination_liquidity
16 collateral_token_program
17 repay_liquidity_token_program
18 withdraw_liquidity_token_program
19 instruction_sysvar_account

Args:
- liquidity_amount_native
- min_acceptable_received_liquidity_amount_native
- max_allowed_ltv_override_percent_raw

Any other account count or instruction data shorter than 32 bytes:
`KAMINO_FIELD_LAYOUT_UNRESOLVED_FAIL_CLOSED`.

No decimals, token price, USD value or profitability may be derived.

## Save11

Exact tag:
`0x11`.

The raw account vector and raw instruction bytes are preserved for every event.

### Public-layout-supported interval

Public SDK constructor first appears at commit
`d01b24d70b24638bc8544a34e3c244918f797122`,
dated 2024-08-06T11:54:18Z.

For event timestamp >= that source time, require:
- exactly 15 accounts;
- instruction bytes length >= 9;
- first byte `0x11`.

Fields:
0 source_liquidity
1 destination_collateral
2 destination_reward_liquidity
3 repay_reserve
4 repay_reserve_liquidity_supply
5 withdraw_reserve
6 withdraw_reserve_collateral_mint
7 withdraw_reserve_collateral_supply
8 withdraw_reserve_liquidity_supply
9 withdraw_reserve_fee_receiver
10 obligation
11 lending_market
12 lending_market_authority
13 transfer_authority
14 token_program

Argument:
- liquidity_amount_native = little-endian u64 bytes [1:9].

### Pre-public-layout interval

For 2024-07-19T19:30:52Z <= timestamp < 2024-08-06T11:54:18Z:
- preserve exact raw account vector;
- preserve exact raw instruction data;
- record account_count;
- preserve bytes [1:9] as `raw_arg_u64_0` only if structurally available;
- DO NOT assign later account names or call the u64 `liquidity_amount` solely from later source.

Classification:
`SAVE11_FIELD_LAYOUT_PENDING_RAW_RECONCILIATION`.

This is not a failed event and does not remove it from the event census.

## Completeness

Enrichment passes only if:
- every census instruction key is re-found exactly once;
- no extra source instruction key appears;
- all Kamino rows resolve to an authorized structural layout;
- Save11 rows at/after 2024-08-06 resolve to exact 15-account layout;
- pre-2024-08-06 Save11 rows are explicitly retained as pending rather than silently mapped;
- raw account/data hashes are persisted;
- no source anomaly is observed.

Classification:
- `FIELD_ENRICHMENT_COMPLETE_WITH_SAVE11_PRELAYOUT_PENDING` when only the explicitly allowed Save11 pre-layout interval remains unresolved;
- `FIELD_ENRICHMENT_COMPLETE` when no unresolved fields remain;
- `FIELD_ENRICHMENT_FAIL_CLOSED` on mismatch/anomaly;
- `FIELD_ENRICHMENT_TRANSPORT_BLOCKED` on transport exhaustion.

## Firewall

Source fields only.

Forbidden: prices, token USD values, returns, PnL, future direction, economic outcome testing, performance-based event filtering, trading, orders, wallets, exchange mutation, paid sources, account creation, merge main.
