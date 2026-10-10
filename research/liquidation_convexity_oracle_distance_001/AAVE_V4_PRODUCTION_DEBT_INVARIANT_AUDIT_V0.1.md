# LCOD-001 AAVE V4 PRODUCTION DEBT INVARIANT AUDIT V0.1

Date: 2026-09-25
Purpose: establish whether Borrow-event history can define a complete candidate
superset for block-pinned active-debt population reconstruction.

## Pinned source

Repository: aave/aave-v4
Commit: 40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f

Address book:
Repository: aave-dao/aave-address-book
Commit: f08dbd218a1da7ea1ac3bb0e387652fdb9f98042

## Lending Spoke universe

Pinned AaveV4Ethereum.getAllSpokes() returns exactly 13 lending Spokes:
1. BLUECHIP_SPOKE
2. ETHENA_CORRELATED_SPOKE
3. ETHENA_ECOSYSTEM_SPOKE
4. FOREX_SPOKE
5. GOLD_SPOKE
6. LOMBARD_BTC_SPOKE
7. MAIN_SPOKE
8. PAXG_GOLD_SPOKE
9. USDG_PENDLE_SPOKE
10. ETHERFI_ESPOKE
11. KELP_ESPOKE
12. LIDO_ESPOKE
13. USDG_MAPLE_ESPOKE

TREASURY_SPOKE and tokenization spokes are not returned by getAllSpokes() and
are not part of this lending-debt population gate.

## Production mutation audit

Pinned src/spoke/Spoke.sol:

### Debt creation / increase

borrow(reserveId, amount, onBehalfOf):
- resolves UserPosition storage _userPositions[onBehalfOf][reserveId];
- calls hub.draw(...);
- executes:
  userPosition.drawnShares += drawnShares.toUint120();
- sets borrowing status when required;
- refreshes/validates account risk;
- emits:
  Borrow(reserveId, msg.sender, onBehalfOf, drawnShares, amount).

Therefore the owner of every debt increase is present as indexed Borrow.user.

### Debt reduction

repay(...):
- calculates restored debt;
- executes:
  userPosition.drawnShares -= restoredShares.toUint120();
- may clear borrowing status;
- emits Repay.

LiquidationLogic:
- reduces userPosition.drawnShares by liquidated drawn shares;
- may clear borrowing state;
- deficit reporting removes/handles remaining bad debt rather than creating new
  user debt.

### Search for alternative debt creation

Repository searches across production src/ for:
- drawnShares assignments/increments;
- direct user-position setters;
- debt transfer/migration;
- position transfer;
found no production path that creates or transfers user drawnShares without
the Spoke.borrow path.

Direct setters of debt fields found by search are confined to test/mock helpers,
not production src/.

Position managers and gateways call ISpoke.borrow rather than mutating Spoke
user debt storage directly.

## Frozen invariant

Under the pinned production implementation:

ACTIVE_USER_DEBT_AT_BLOCK_N
=> at least one prior Borrow event for the same (Spoke, user) at block <= N.

Borrow history is therefore a candidate SUPERSET, not the final active set.
Repay/liquidation mean many historical Borrow users will no longer have debt.

The final active set must always be filtered with block-N
getUserAccountData(user).totalDebtValueRay > 0 on the same Spoke.

## Empirical contradiction gate

The separate BORROW_EVENT_BLOCK_PINNED_POPULATION_GATE must additionally require
every current official Aave MCP borrow-holder pair to exist in full Borrow-event
history. Any missing current pair invalidates this invariant for operational use
and forces SOURCE_BLOCKED.

## Boundaries

This audit establishes source/population logic only.
It does not establish:
- a liquidation-convexity curve;
- market predictiveness;
- liquidation outcomes;
- PnL;
- live execution.
