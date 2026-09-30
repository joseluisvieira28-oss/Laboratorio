# DLS — MARGINFI -> ORCA WHIRLPOOLS SIGNED-FLOW CALIBRATION V0.1 — PRE-DECODE FREEZE

Date: 2026-09-30
Branch: dls-marginfi-route-migration-v01
Status: FROZEN SOURCE-ONLY BEFORE ORCA INSTRUCTION DATA / DIRECTION IS OPENED

Family:
DLS-MARGINFI-ORCA-SIGNED-FLOW-001

Parent source authority:
MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_PASS

Parent run:
36769933849

Monthly immutable route samples:
- August artifact ID 11123323570
- September artifact ID 11122359266

Orca program:
whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc

## Official decoder authority

Upstream repository:
orca-so/whirlpools

Pinned upstream commit:
f4b99e79e7140f3917e4ce81a2e8ad06ccdf8ce4

Authoritative files:
- programs/whirlpool/src/lib.rs
- programs/whirlpool/src/state/whirlpool.rs
- programs/whirlpool/src/instructions/swap.rs
- programs/whirlpool/src/instructions/two_hop_swap.rs
- programs/whirlpool/src/instructions/v2/swap.rs
- programs/whirlpool/src/instructions/v2/two_hop_swap.rs
- rust-sdk/client/src/generated/instructions/swap.rs
- rust-sdk/client/src/generated/instructions/swap_v2.rs
- rust-sdk/client/src/generated/instructions/two_hop_swap.rs
- rust-sdk/client/src/generated/instructions/two_hop_swap_v2.rs

Official program ID:
whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc

Official instruction discriminators:

swap:
f8c69e91e17587c8

swap_v2:
2b04ed0b1ac91e62

two_hop_swap:
c360ed6c44a2dbe6

two_hop_swap_v2:
ba8fd11dfe02c275

Official Whirlpool account discriminator:
3f95d10ce1806309

## Official direction semantics

For single-pool swap / swap_v2:

a_to_b = true:
input = token_mint_a
output = token_mint_b

a_to_b = false:
input = token_mint_b
output = token_mint_a

For two-hop variants:
- hop one output mint must equal hop two input mint;
- route input is hop-one input;
- route output is hop-two output.

## Frozen wire decoding

Solana instruction data is decoded from SQD instruction.data using the same raw-transport candidate
policy already used elsewhere in DLS:
- hex / 0xhex
- base58
- base64

Exactly one candidate must match one official discriminator.
Multiple conflicting decodes => SOURCE_EVIDENCE_INCOMPLETE.

### swap / swap_v2 arguments

After 8-byte discriminator:

u64 amount
u64 other_amount_threshold
u128 sqrt_price_limit
bool amount_specified_is_input
bool a_to_b

Therefore:
- amount_specified_is_input is raw byte offset 40
- a_to_b is raw byte offset 41

Booleans must be exactly 0 or 1.

### two_hop_swap / two_hop_swap_v2 arguments

After 8-byte discriminator:

u64 amount
u64 other_amount_threshold
bool amount_specified_is_input
bool a_to_b_one
bool a_to_b_two
u128 sqrt_price_limit_one
u128 sqrt_price_limit_two
[optional remaining-accounts info for V2]

Therefore:
- amount_specified_is_input offset 24
- a_to_b_one offset 25
- a_to_b_two offset 26

Booleans must be exactly 0 or 1.

## Frozen account semantics

### swap

Required account order:
0 token_program
1 token_authority
2 whirlpool
3 token_owner_account_a
4 token_vault_a
5 token_owner_account_b
6 token_vault_b
7 tick_array_0
8 tick_array_1
9 tick_array_2
10 oracle

Pool address = account[2].

### swap_v2

Required account order:
0 token_program_a
1 token_program_b
2 memo_program
3 token_authority
4 whirlpool
5 token_mint_a
6 token_mint_b
7 token_owner_account_a
8 token_vault_a
9 token_owner_account_b
10 token_vault_b
11 tick_array_0
12 tick_array_1
13 tick_array_2
14 oracle

Mints are source-direct:
A = account[5]
B = account[6].

### two_hop_swap

Required leading account order:
0 token_program
1 token_authority
2 whirlpool_one
3 whirlpool_two
...

Pool one = account[2].
Pool two = account[3].

### two_hop_swap_v2

Required leading account order:
0 whirlpool_one
1 whirlpool_two
2 token_mint_input
3 token_mint_intermediate
4 token_mint_output
...

Route endpoints are source-direct:
input = account[2]
intermediate = account[3]
output = account[4].

## Legacy pool-mint authority

For legacy swap and two_hop_swap only, token mints are not instruction accounts.

Retrieve each referenced Whirlpool account using Solana mainnet RPC getMultipleAccounts.

Accept a pool account only if:
- account owner equals Orca Whirlpools program ID;
- raw account data begins with official Whirlpool discriminator 3f95d10ce1806309;
- raw account length is compatible with official Whirlpool layout.

Pinned official layout from Whirlpool state:

after account discriminator:
whirlpools_config 32
whirlpool_bump 1
tick_spacing 2
fee_tier_index_seed 2
fee_rate 2
protocol_fee_rate 2
liquidity 16
sqrt_price 16
tick_current_index 4
protocol_fee_owed_a 8
protocol_fee_owed_b 8
token_mint_a 32
token_vault_a 32
fee_growth_global_a 16
token_mint_b 32
token_vault_b 32

Thus raw byte offsets:
token_mint_a = [101,133)
token_mint_b = [181,213)

The Whirlpool program initializes these mint fields as pool identity fields.
This calibration uses current on-chain account bytes only to recover those immutable pool endpoint
identities. Any missing/invalid pool account => SOURCE_EVIDENCE_INCOMPLETE.

RPC transport source:
https://api.mainnet-beta.solana.com

No price or pool-price field is read.

## Canonical Marginfi endpoint authority

For each sampled transaction:
- recover canonical Marginfi field-enrichment row by exact signature + canonical instructionAddress;
- asset mint must map to native wrapped SOL:
  So11111111111111111111111111111111111111112
- liability mint comes from the source-authoritative Marginfi bank registry.

Bank registry:
run 36312418451
artifact ID 10929339072

## Frozen calibration population

Use immutable route-migration monthly receipts.

For August independently:
1. take rows whose after_unique_programs includes exact Orca program ID;
2. rank ascending SHA256(signature + "|" + canonical-json(instructionAddress));
3. select first 32.

For September independently:
same rule, first 32.

Total calibration sample = exactly 64.

This selection uses source program presence only.
No instruction data, direction, token amount, price, return or PnL participates.

## Exact transaction binding

For each sample:
- query exact finalized slot;
- recover exact successful parent transaction by signature;
- bind canonical Marginfi liquidation by exact program ID + instructionAddress;
- retain only successful committed Orca instructions strictly AFTER the canonical Marginfi instruction.

All post-liquidation Orca instructions must be adjudicated.

## Frozen route adjudication

Decode every supported Orca swap instruction strictly after the liquidation in canonical
instructionAddress order.

For each decoded instruction derive:
- input mint
- output mint
- amount_specified_is_input
- amount argument
- exact_input_amount only if amount_specified_is_input=true.

If multiple decoded Orca swaps exist in one transaction:
- require ordered simple mint chain:
  output_i == input_(i+1)
- no repeated input/output pair
- no repeated mint/cycle.

Route endpoints:
I = first input mint
O = final output mint.

If I = Marginfi asset mint (SOL) and O = Marginfi liability mint:
COLLATERAL_TO_LIABILITY_ORCA_PROVEN
asset = SIGNED_SELL_PRESSURE_PROVEN
liability = SIGNED_BUY_PRESSURE_PROVEN.

If I = liability mint and O = SOL:
LIABILITY_TO_COLLATERAL_ORCA_PROVEN
liability = SIGNED_SELL_PRESSURE_PROVEN
asset = SIGNED_BUY_PRESSURE_PROVEN.

If source-complete route endpoints are neither:
DIRECTION_AMBIGUOUS.

Unsupported Orca non-swap instruction after liquidation does not itself establish direction.
If a transaction contains Orca presence but no supported swap instruction:
SOURCE_EVIDENCE_INCOMPLETE.

## Amount authority

Route direction does not require exact realized amount.

For a one-instruction route:
exact input amount is source-proven only when amount_specified_is_input=true.

For a chained route:
exact route input amount is source-proven only when the first decoded swap has
amount_specified_is_input=true.

Otherwise:
direction may still be proven but exact_input_amount is UNPROVEN.

No estimate or price conversion is allowed.

## Calibration PASS

MARGINFI_ORCA_SIGNED_FLOW_CALIBRATION_PASS only if ALL:

1. sample_count = 64;
2. August sample = 32;
3. September sample = 32;
4. exact transaction recovery = 64;
5. source_evidence_incomplete <= 3;
6. source-complete route count >= 61;
7. direction-proven among source-complete >= 90%;
8. contradictions = 0;
9. identity conflicts = 0.

Exact input-amount availability is reported but is NOT a PASS criterion.

PASS authorizes a separately frozen full Orca source census.
PASS does NOT authorize market returns.

Otherwise:
MARGINFI_ORCA_SIGNED_FLOW_CALIBRATION_PARTIAL
or
MARGINFI_ORCA_SIGNED_FLOW_CALIBRATION_BLOCKED for transport/identity/source conflicts.

## Firewall

prices=false
ohlc=false
returns=false
pnl=false
market_2024_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_decode_tuning=false
