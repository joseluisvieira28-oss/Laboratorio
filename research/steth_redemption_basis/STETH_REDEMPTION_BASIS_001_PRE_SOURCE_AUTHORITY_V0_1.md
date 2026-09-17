# STETH-REDEMPTION-BASIS-001 — PRE-SOURCE AUTHORITY V0.1

Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**  
Date: **2026-09-17**  
Repository: `joseluisvieira28-oss/Laboratorio`  
Branch: `empty-territory-hunt-v0.1`

## 1. Governance

Research-only. Fail-closed. This authority permits source/provenance work only.

Forbidden until a separately recorded `SOURCE_DATA_PASS`:
- future price/return inspection;
- PnL, win rate, profit factor, drawdown or strategy performance;
- 2025 or 2026 data;
- live trading, exchange/wallet mutation, orders, execution webhooks;
- merge to `main`;
- parameter, threshold, direction, horizon or cost rescue after outcomes.

Flags:
- `PRICE_OUTCOMES_ALLOWED=false`
- `RETURNS_ALLOWED=false`
- `PNL_ALLOWED=false`
- `2025_ACCESS_ALLOWED=false`
- `2026_ACCESS_ALLOWED=false`

## 2. Provisional lab identity

- LAB_ID: `STETH-REDEMPTION-BASIS-001`
- Primary family: `MR`
- Secondary family: `RV`
- Mechanism: primary-redemption anchored convergence between secondary-market stETH and protocol-level ETH redemption value.

## 3. Economic mechanism

Lido V2 enables in-protocol stETH -> ETH withdrawals through an asynchronous FIFO withdrawal queue. stETH locked in the queue stops earning staking rewards until finalization. Therefore a secondary-market seller can rationally accept a discount to receive immediate ETH rather than wait for protocol redemption and bear queue/protocol risk.

The proposed edge is not directional ETH forecasting. The economic object is the spread between:
1. the amount of stETH obtainable for a fixed ETH notional on an executable secondary-market path; and
2. the ETH ultimately claimable through Lido redemption;
minus queue opportunity cost, gas and explicit execution costs.

Economic counterparty: impatient / liquidity-constrained stETH sellers and holders assigning a positive value to immediate exit versus asynchronous redemption.

## 4. Novelty firewall

This is not `ETH-STAKING-FLOW-001`.

`ETH-STAKING-FLOW-001` studies validator entry-versus-exit queue pressure as a predictor of future ETH returns. This lab studies an asset-specific redemption cash-flow anchor and does not use validator net-entry queue pressure as its signal.

This is not `STABLECOIN-PEG-DISLOCATION-001`.

The equilibrium is not a fiat peg. The anchor is an explicit protocol redemption path with an endogenous waiting cost and foregone staking reward.

No existing lab may be relabelled or reopened by this authority.

## 5. Frozen source period

Source window only:
- start: `2023-05-15T00:00:00Z`
- end: `2024-12-31T23:59:59Z`

Rationale: Lido V2 Ethereum withdrawals launched on 2023-05-15. 2025 and 2026 remain protected.

Expected calendar snapshots if later Discovery uses one daily 12:00 UTC observation: **597**.

## 6. Canonical source objects

Ethereum mainnet only (`chainId=1`).

Lido:
- stETH proxy: `0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84`
- WithdrawalQueueERC721 proxy: `0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1`
- canonical events required: `WithdrawalRequested`, `WithdrawalsFinalized`, `WithdrawalClaimed`, `TokenRebased`

Secondary execution venue for V0.1:
- Curve legacy ETH/stETH pool: `0xDC24316b9AE028F1497c275EB9192a3Ea0f67022`
- required historical state methods: `get_dy`, `fee`
- required event family: `TokenExchange`

Transport may use a public Ethereum archival JSON-RPC only if it can reproduce historical contract code, logs and `eth_call` state at the frozen blocks. Transport is not the authority; Ethereum mainnet contract state/events are the authority.

## 7. Source-only gate objective

Before any economic outcome is opened, prove:
1. contract identities and deployment provenance;
2. historical state accessibility across both ends of the frozen source period;
3. bounded historical event retrieval for all required event families;
4. historical `eth_call` support for the Curve execution quote/fee methods and Lido queue-state methods;
5. deterministic timestamp-to-block mapping;
6. stable identifiers (`blockHash`, `transactionHash`, `logIndex`) sufficient for deduplication;
7. no dependency on token survivorship lists or present-day symbol membership;
8. the source path can be reproduced without querying 2025/2026.

## 8. Fail-closed classifications

Only these source-stage states are permitted:
- `SOURCE_DATA_PASS`
- `SOURCE_AUTH_BLOCKED`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `DATA_FAILURE`
- `PROVENANCE_FAILURE`
- `INSUFFICIENT_SOURCE_COVERAGE`

`NO_EDGE` is forbidden at this phase.
