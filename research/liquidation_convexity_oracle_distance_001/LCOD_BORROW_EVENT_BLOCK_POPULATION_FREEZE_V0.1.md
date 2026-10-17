# LCOD BORROW-EVENT BLOCK-PINNED POPULATION GATE V0.1

Frozen: 2026-09-25
Stage: SOURCE / POPULATION COMPLETENESS
Market/liquidation outcomes: CLOSED

## Pinned authorities

Aave V4 protocol source:
- repository: aave/aave-v4
- commit: 40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f

Ethereum V4 address book:
- repository: aave-dao/aave-address-book
- commit: f08dbd218a1da7ea1ac3bb0e387652fdb9f98042

The address-book getAllSpokes() returns exactly 13 Ethereum lending Spokes.

## Production debt-creation invariant

Pinned production Spoke.sol was audited before this gate.

Observed production mutation paths:
- borrow(): userPosition.drawnShares += drawnShares and then emits
  Borrow(reserveId, caller, onBehalfOf, drawnShares, amount).
- repay(): userPosition.drawnShares -= restoredShares.
- liquidation path: reduces drawnShares / may report deficit.
- no production user-debt transfer or direct setter was identified.
- direct debt setters found by repository search are test/mock-only.

Therefore every user/spoke pair with protocol-created debt must have appeared in
at least one Borrow event at that Spoke before the debt can remain active.

If this invariant is contradicted by live-source evidence, FAIL CLOSED.

## Official 13-Spoke universe

Use exactly the 13 addresses returned by the pinned AaveV4Ethereum.getAllSpokes:
BLUECHIP, ETHENA_CORRELATED, ETHENA_ECOSYSTEM, FOREX, GOLD, LOMBARD_BTC,
MAIN, PAXG_GOLD, USDG_PENDLE, ETHERFI_ESPOKE, KELP_ESPOKE, LIDO_ESPOKE,
USDG_MAPLE_ESPOKE.

TREASURY_SPOKE and tokenization spokes are not lending Spokes and are excluded.

## Event source

Borrow event signature:
Borrow(uint256,address,address,uint256,uint256)

For every pinned lending Spoke, enumerate every Borrow log available on Ethereum
from genesis through the run's latest block using an archive log transport.
The indexed user is topic[3].

Retain raw transport SHA256 and event counts. Durable receipts retain only
hashed user/pair identities, never raw wallets.

## Block-pinned census

Choose one Ethereum finalized block N at run start.

Candidate set at N:
all unique (spoke,user) pairs with >=1 Borrow event at block <= N.

For every candidate pair, call getUserAccountData(user) at that exact Spoke and
exact block N. Pair is ACTIVE_DEBT_AT_N iff totalDebtValueRay > 0.

All scientific calls used for active filtering must use N.

## Independent current-source contradiction check

Separately enumerate current V4 borrow holders using the official Aave MCP
get_markets + get_reserve_holders route and decode each reserveId to
(spoke,reserve).

Every current MCP (spoke,user) borrower pair MUST exist somewhere in the full
Borrow-event history through latest. This check is only a contradiction test;
it does not define the block-N population.

## PASS

BORROW_EVENT_BLOCK_CENSUS_PASS requires:
- all 13 official Spokes queried;
- zero event parse/source errors;
- >=1 Borrow event;
- zero current MCP borrower pairs missing from full Borrow history;
- zero unresolved block-N eth_call errors;
- >=1 active-debt pair at N.

Passing proves a block-pinned active-debt population source under the frozen
production invariant. It authorizes component reconstruction over that exact
population at N.

It does NOT authorize market outcomes, liquidation outcomes or live execution.
