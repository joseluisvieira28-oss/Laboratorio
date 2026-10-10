# LCOD BLOCK-PIN SNAPSHOT GATE V0.1 — PRE-EXECUTION FREEZE

Frozen: 2026-09-24
Stage: SOURCE / SNAPSHOT CONSISTENCY
Market and liquidation outcomes: CLOSED

## Trigger

The current Aave MCP route can reconcile per-borrower V4 health factors, but it
does not expose a block parameter for get_user_positions, get_position_items,
get_user_summary or get_reserve_details.

The full-census live read therefore cannot automatically be called one
simultaneous protocol snapshot.

This gate is independent of the fresh-price census reconciliation V0.2.

## Pinned official authorities

Aave V4 core:
- repository: aave/aave-v4
- commit: 40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f

Aave Address Book:
- repository: aave-dao/aave-address-book
- commit: f08dbd218a1da7ea1ac3bb0e387652fdb9f98042

Official ISpoke at the pinned V4 commit exposes:
- getReserve(reserveId)
- getDynamicReserveConfig(reserveId, dynamicConfigKey)
- getUserReserveStatus(reserveId, user)
- getUserSuppliedAssets(reserveId, user)
- getUserDebt(reserveId, user)
- getUserAccountData(user)
- ORACLE()

Official IAaveOracle exposes getReservesPrices(reserveIds).

All are view calls and may be queried using eth_call with one explicit block tag.

## Initial Ethereum spoke authority

Pinned address-book Ethereum V4 spokes include, among others:
- MAIN_SPOKE: 0x94e7A5dCbE816e498b89aB752661904E2F56c485
- BLUECHIP_SPOKE: 0x973a023A77420ba610f06b3858aD991Df6d85A08

No spoke is selected for science by name or apparent risk. A first feasibility
fixture may use the first current debt-bearing borrower encountered on an
officially enumerated Ethereum V4 spoke, solely to prove block-pinned parity.

## Required block-pinned fixture

1. choose block N = latest finalized/safely confirmed Ethereum block at probe start;
2. every eth_call in the fixture MUST use block tag N;
3. resolve one current debt-bearing borrower and spoke before the block-pinned
   calculation, but do not retain raw wallet address in durable evidence;
4. at block N read:
   - reserve structs;
   - user reserve status;
   - supplied assets;
   - drawn + premium debt;
   - user position dynamicConfigKey where needed;
   - dynamic collateral config;
   - oracle reserve prices;
   - official getUserAccountData healthFactor;
5. reconstruct HF from only block-N values;
6. compare to block-N official healthFactor using the already frozen <=5e-5
   relative-error tolerance.

## PASS

BLOCK_PIN_FIXTURE_PASS if:
- all calls are proven to use one identical block number/hash;
- reconstructed HF passes <=5e-5;
- zero latest/current fallback occurs;
- raw call inputs/output hashes are retained;
- no transaction, signing, mutation or outcome access occurs.

Passing only proves same-block snapshot plumbing.

## Next stage after PASS

Only after a block-pinned fixture passes may LCOD design a block-pinned
protocol-wide snapshot. The census population/source coverage gate remains
separate.

No curve, shock point, liquidation outcome, market response or PnL may be opened
by this gate.
