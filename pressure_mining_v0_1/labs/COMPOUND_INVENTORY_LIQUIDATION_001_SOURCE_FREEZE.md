# COMPOUND-INVENTORY-LIQUIDATION-001 — SOURCE / MECHANISM FREEZE V0.1

Status: FROZEN_SOURCE_FIRST / OUTCOMES LOCKED
Primary family: CREDIT
Secondary family: MICRO

## Mechanism

Compound III liquidations create a two-stage balance-sheet process:

1. an underwater borrower is absorbed; the protocol uses base reserves to extinguish the debt and receives collateral;
2. when reserve conditions permit, the seized collateral can be purchased from the protocol at a discount through buyCollateral.

Frozen research primitive:
**protocol-owned seized-collateral inventory + inventory disposal flow**.

This is not the same observable as borrower health-factor crowding and not the same contract as generic liquidation-event intensity.

## Who pays / acts

- distressed borrowers are involuntarily absorbed;
- Compound protocol reserves temporarily warehouse collateral;
- liquidators/arbitrageurs purchase that inventory at protocol-quoted discounts.

## Source authority

Official documentation:
- https://docs.compound.finance/liquidation/
- https://github.com/compound-finance/comet
- official deployment roots under deployments/<network>/<deployment>/roots.json

Primary chain for V0.1 source probe: Ethereum mainnet / USDC Comet.

## Source Gate only

Required PASS:
- official root file resolves a Comet proxy address;
- contract bytecode exists;
- official source contains AbsorbCollateral and BuyCollateral event definitions;
- permission-clean public RPC can read logs for the Comet address;
- raw source payloads can be hashed and preserved.

No requirement yet:
- minimum event N;
- event economics;
- asset response;
- direction;
- holding period;
- fees/slippage;
- PnL.

## Novelty firewall

Forbidden:
- reinterpret existing Aave outcomes;
- inherit promotion credit from Aave/L2/DeFi Liquidation labs;
- choose collateral after seeing returns;
- define a post-outcome price direction.

Any future Discovery requires a separate pre-outcome protocol after source/event census.

## Failure classes

SOURCE_PASS
SOURCE_PARTIAL
SOURCE_BLOCKED
PROVENANCE_FAILURE
TECHNICAL_FAILURE

NO_EDGE is impossible at this stage.
