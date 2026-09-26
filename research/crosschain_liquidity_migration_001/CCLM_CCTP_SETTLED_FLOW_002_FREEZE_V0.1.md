# CCLM-CCTP-SETTLED-FLOW-002 — PRE-OUTCOME SOURCE FREEZE V0.1

Frozen: 2026-09-24
Parent family: CROSSCHAIN-LIQUIDITY-MIGRATION-001
Sibling retained unchanged: CCLM-CCTP-USDC-001

## Why this is a distinct child, not a rescue

CCLM-CCTP-USDC-001 asks whether source-chain burns can be paired to destination
settlements. Its original source-smoke remains SOURCE_SMOKE_PARTIAL and its
18.75% settlement result is preserved.

This child measures a different economic event boundary:

destination MessageReceived + same-transaction MintAndWithdraw
= completed native-USDC migration.

Unsettled source burns are therefore not treated as missing data or completed
capital migration.

No market outcome has been opened for either child.

## Canonical completed-flow event

A destination-chain event is SETTLED_FLOW_CANONICAL only if:
1. MessageReceived is emitted by the pinned destination MessageTransmitter;
2. sourceDomain is the opposite frozen domain in {0,1};
3. sender equals the pinned source TokenMessenger as bytes32;
4. V1 burn body is exactly 132 bytes and body version=0;
5. burnToken equals pinned native USDC on the source chain;
6. in the same destination transaction there is exactly one MintAndWithdraw at
   the pinned destination TokenMessenger;
7. minted token equals pinned native USDC on destination;
8. mint recipient and exact amount equal the V1 burn body.

## Frozen routes

- Ethereum/domain 0 -> Avalanche/domain 1
- Avalanche/domain 1 -> Ethereum/domain 0

## Frozen smoke window

Destination settlement UTC day:
2023-08-20T00:00:00Z through 2023-08-20T23:59:59Z

This date is a source-method fixture inherited from the sibling smoke work.
It is not chosen from a market outcome.

## PASS

SOURCE_SETTLED_FLOW_SMOKE_PASS requires:
- >=1 canonical settled flow on at least one frozen route;
- zero semantic mismatches among accepted events;
- raw transport hashes retained;
- no market returns/PnL opened.

This proves only that completed directional CCTP V1 migration can be
reconstructed historically.
