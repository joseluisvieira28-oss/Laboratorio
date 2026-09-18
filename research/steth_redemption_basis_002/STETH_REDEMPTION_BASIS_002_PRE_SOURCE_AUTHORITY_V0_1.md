# STETH-REDEMPTION-BASIS-002 — PRE-SOURCE AUTHORITY V0.1

Date: 2026-09-18
Status: FROZEN / SOURCE-ONLY / OUTCOME-BLIND
Branch: steth-redemption-basis-002-source-v0.1

## Lineage and anti-rescue boundary

STETH-REDEMPTION-BASIS-001 V0.1 is terminal:
FROZEN_SOURCE_BOUNDARY_PROVENANCE_FAILURE.

It is not reopened, amended or rescued.

The decisive V0.1 provenance probe proved:
- frozen 2023-05-15T12:00:00Z snapshot mapped to block 17,265,042;
- WithdrawalQueue proxy code existed but getLastRequestId() reverted on 3/3 archive providers;
- canonical V2 activation transaction was available with quorum at block 17,266,004;
- getLastRequestId() was accessible at activation on 3/3 providers.

Source evidence:
run 35385142825
artifact 10563801890
digest sha256:a1a47e2c1026cccfc068b6d42a0f699dfd527aa038d4b2f74a2d904a6089d741

This successor receives a new LAB_ID and a new frozen source boundary before any new source acquisition.

## Lab identity

LAB_ID: STETH-REDEMPTION-BASIS-002
Primary family: MR
Secondary family: RV

Economic mechanism remains a protocol-redemption convergence anchor:
secondary-market stETH can trade at a discount to the ETH value ultimately claimable through Lido withdrawal, while queue waiting time, foregone staking reward, gas, execution cost and protocol risk can justify a nonzero discount.

No market-price or performance claim is made at this stage.

## Objective source clock

The source clock is not selected by historical performance.

Rule frozen before source acquisition:
use the first scheduled daily 12:00 UTC snapshot STRICTLY AFTER the canonically proven V2 activation block/time.

The predecessor's activation proof establishes that 2023-05-15 12:00 UTC is pre-activation.
Therefore:

first frozen snapshot:
2023-05-16T12:00:00Z

last frozen snapshot:
2024-12-31T12:00:00Z

daily clock:
12:00 UTC

expected daily snapshot population:
596

No snapshot may be removed after source or outcome inspection.

2025 and 2026 remain forbidden.

## Canonical contracts

Ethereum mainnet only.

stETH proxy:
0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84

WithdrawalQueueERC721 proxy:
0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1

Curve legacy ETH/stETH pool:
0xDC24316b9AE028F1497c275EB9192a3Ea0f67022

Canonical V2 activation transaction:
0x592d68a259af899fb435da0ac08c2fd500cb423f37f1d8ce8e3120cb84186b21

Expected activation block from predecessor provenance:
17,266,004

## Frozen source gate

A. Chain and activation provenance
- chainId = 1;
- activation receipt must be available from at least 2 of the frozen 3 archive providers;
- activation block must agree and equal 17,266,004.

B. Exact first/last snapshot mapping
- map 2023-05-16T12:00:00Z and 2024-12-31T12:00:00Z to first block at/after each timestamp;
- at least 2 providers must agree on each mapped block.

C. Historical bytecode
At both mapped edge blocks, non-empty code is required for:
- stETH;
- WithdrawalQueue;
- Curve ETH/stETH pool.

D. Historical state-call accessibility
At both mapped edge blocks, at least 2 providers must return non-empty valid responses for:
- Curve get_dy(int128,int128,uint256) with fixed 10 ETH notional;
- Curve fee();
- WithdrawalQueue getLastRequestId();
- WithdrawalQueue getLastFinalizedRequestId();
- WithdrawalQueue unfinalizedStETH().

Economic numeric values must not be printed or interpreted. Record accessibility only.

E. Bounded event provenance
Using Ethereum mainnet structural log source, recover at least one canonical log across the union of frozen early/late bounded windows for each:
- WithdrawalRequested(uint256,address,address,uint256,uint256)
- WithdrawalsFinalized(uint256,uint256,uint256,uint256,uint256)
- WithdrawalClaimed(uint256,address,address,uint256)
- TokenRebased(uint256,uint256,uint256,uint256,uint256,uint256,uint256)
- TokenExchange(address,int128,uint256,int128,uint256)

Record only counts and canonical identity hashes. Do not decode economic payloads.

F. Identifier and protected-period integrity
- canonical log identities unique;
- block/timestamp boundaries valid;
- no block after 2024-12-31T12:00:00Z edge mapping;
- no 2025/2026 traversal.

## Source classifications

SOURCE_DATA_PASS
SOURCE_ACQUISITION_TECHNICAL_FAILURE
PROVENANCE_FAILURE
INSUFFICIENT_SOURCE_COVERAGE

NO_EDGE is forbidden at source stage.

## Next gate

SOURCE_DATA_PASS authorizes only preparation of a separate FINAL_PRE_DISCOVERY_PROTOCOL.

It does NOT authorize:
- predictor computation;
- ETH/stETH basis;
- future return;
- PnL;
- signal performance;
- 2025/2026;
- live trading.

## Hard firewall

No market prices.
No returns.
No PnL/PF/win-rate/drawdown.
No 2025/2026.
No wallets.
No orders.
No exchange mutation.
No main merge.
