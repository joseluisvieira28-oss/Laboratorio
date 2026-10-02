# DLS ROUTE A5A — SOL ROLE ACCOUNT REGISTRY EXTENSION FREEZE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE-ONLY / PROTECTED-2025 OUTCOMES CLOSED
Lab: DEFI-LIQUIDATION-SHOCK-001
Branch: dls-field-enrichment-v01

## Purpose

Prove a complete source-authoritative superset of every SOL role account that could enter the frozen
2025 directional population before any 2025 price/return/PnL is opened.

This gate is required after ROUTE_A5A_SOL_ACCOUNT_EQUIVALENCE_PASS and before any protected-2025
account-filter acquisition.

The prior 13-account 2024 set is retained by construction but is NOT assumed complete for 2025.

## Source logic

Discover accounts from protocol account-creation instructions, not from 2025 liquidation outcomes.

The census runs from each protocol's already-supported historical lower boundary through:
2026-01-01T00:00:00Z exclusive.

Every successful creation instruction is inspected. If its source-authoritative liquidity mint is
wrapped SOL:
So11111111111111111111111111111111111111112

the relevant role account is added to the registry.

This catches an account even if:
- it never liquidated before 2025;
- it was later deprecated/closed;
- it existed only transiently.

No event is selected from price behavior.

## Marginfi authority

Program:
MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA

Historical lower boundary:
2023-02-07T15:47:04Z

Creation instructions included:
1. lending_pool_add_bank
   Anchor discriminator hex: d744484ed0da67b6
   bank_mint = fixed account 5
   bank = fixed account 6
2. lending_pool_add_bank_with_seed
   Anchor discriminator hex: 4cd3d5ab754e9e4c
   bank_mint = fixed account 5
   bank = fixed account 6
3. lending_pool_add_bank_permissionless
   Anchor discriminator hex: 7fbb7922bba7ee66
   bank_mint = fixed account 3
   bank = fixed account 8

Permissionless creation is included even though protocol source constrains it to single-pool LSTs;
if no wrapped-SOL mint appears, it adds no SOL account.

Mainnet clone_bank is not a creation authority because official source explicitly panics on mainnet.

Pinned source authorities:
- pre-existing Crypto Lab Marginfi source authority:
  0dotxyz/marginfi-v2@f6d3d5616e293c9468333571c3ceb90bb2410b00
- current source audit snapshot:
  0dotxyz/marginfi-v2@4e7771e1eec1fd8c321621c08c7524dd4206739d

Frozen liquidation role:
Marginfi asset_bank = liquidation fixed account 1.
Therefore the registry emits the created Bank pubkey.

## Kamino authority

Program:
KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD

Historical lower boundary:
2023-11-17T14:48:24Z

Creation instruction:
init_reserve
Anchor discriminator hex: 8af547e19904032b

Official account roles:
- reserve = fixed account 3
- reserve_liquidity_mint = fixed account 4
- reserve_liquidity_supply = fixed account 5

Pinned source authorities:
- historical V1.6 authority already used by DLS:
  Kamino-Finance/klend@509e98aac6f909cf3e7977e613e503904cf77d00
- current source audit snapshot:
  Kamino-Finance/klend@a08760976f51a3a58c4a0c6ea27b4a0e565bca79

Frozen liquidation collateral-underlying role:
- legacy: account 9 withdraw_reserve_liquidity_supply
- V1.6+: account 11 withdraw_reserve_liquidity_supply

Therefore the registry emits the created reserve_liquidity_supply pubkey when mint=SOL.

## Save / Solend authority

Program:
So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo

Historical lower boundary:
2021-12-08T00:00:00Z

Creation instruction:
InitReserve = instruction byte 2.

Official SDK account roles:
- reserve = fixed account 2
- liquidityMint = fixed account 3
- liquiditySupply = fixed account 4

Pinned source:
- existing DLS independent ABI authority:
  solendprotocol/solend-sdk@c93fbc81fcc68610ad64fbce4a170a38335b7d7f
- current source audit snapshot:
  solendprotocol/solend-sdk@e1ba90c7ba2a685c773d11d7efc5554a67fa8796

Frozen role outputs:
- Save0c liquidation withdraw_reserve account 4 => emit reserve pubkey.
- Save11 liquidation collateral-underlying primary account 8 => emit liquiditySupply pubkey.

## Transport

Preferred source:
official SQD Solana finalized-stream already validated by DLS.

Query only:
- block number/timestamp;
- successful transaction signature/error;
- instruction programId/accounts/data/instructionAddress/isCommitted/error.

No token balances, amounts, oracle values, prices, returns, PnL or market data.

Marginfi and Kamino use exact d8 discriminator filters.
Solend uses the exact first instruction byte 0x02. If the provider lacks a byte-1 server filter,
a program-id stream may be used only if the exact frozen interval terminates deterministically;
otherwise this registry remains SOURCE_BLOCKED. No heuristic sampling.

## Registry construction

Final registry is the UNION of:
1. every source-proven SOL role account created before 2026-01-01 under the rules above;
2. all 13 previously frozen A5 historical SOL role accounts.

Every historical account must either:
- be reproduced by the creation census; or
- remain explicitly grandfathered from the already-frozen pre-2025 source authority with provenance.

No account may be removed because it has zero 2025 events.

Deduplicate exact pubkeys within protocol/role.

## PASS gate

SOL_ROLE_ACCOUNT_REGISTRY_2025_PASS requires:
- all three protocol source scans terminate at exact lower/upper boundaries;
- zero successful matching creation instruction has malformed frozen account shape;
- zero source conflict;
- every SOL-mint creation emits the expected role account(s);
- every one of the 13 historical role accounts is retained;
- source census spans through 2025-12-31;
- at least one account remains for each of:
  marginfi asset_bank,
  save0c withdraw_reserve,
  kamino withdraw_reserve_liquidity_supply,
  save11 withdraw_reserve_liquidity_supply.

Otherwise:
SOL_ROLE_ACCOUNT_REGISTRY_2025_BLOCKED.

## Downstream authority

PASS authorizes only:
- adaptive account-filter source acquisition over 2025;
- the same four frozen liquidation classes;
- the existing 60-second clustering and finalizer.

It does NOT authorize market prices.
Economic holdout remains closed until real PROTECTED_2025_SOURCE_AUTHORITY_PASS.

## Firewall

protected_2025_prices_opened=false
protected_2025_returns_opened=false
protected_2025_pnl_opened=false
protected_2026_outcomes_opened=false
post_outcome_tuning=false
purchases=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE
