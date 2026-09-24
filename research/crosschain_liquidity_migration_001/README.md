# CROSSCHAIN-LIQUIDITY-MIGRATION-001

Child MVE: CCLM-CCTP-USDC-001
Status: M2 SOURCE GATE / PRE-OUTCOME
Opened: 2026-09-24
Primary family: FLOW
Secondary family: LEADLAG

## Why this is not the old #9 source attempt

The 2026-09-14 CROSS-CHAIN CAPITAL MIGRATION reconnaissance targeted DefiLlama bridge-history endpoints and was SOURCE_AUTH_GATED.

This MVE uses a materially different source identity:
Circle Cross-Chain Transfer Protocol (CCTP) native USDC burn/message/mint lifecycle.

Circle documents CCTP as burning native USDC on the source chain and minting native USDC on the destination chain. This provides an explicit directional transfer mechanism rather than an aggregate bridge UI series.

Primary references:
- https://developers.circle.com/cctp
- https://developers.circle.com/api-reference/stablecoins/common/get-attestation

## Research object

source-chain USDC burn/message
    -> cross-chain transfer
    -> destination-chain USDC mint
    -> destination liquidity state

V0.1 stops before any token/BTC/ETH return outcome.

## Governance

- Source-only / mechanism-only.
- No market return or PnL.
- No wallet, bridge, exchange or contract mutation.
- No protected-period outcome opening.
- No merge to main without explicit authority.
- No use of current chain labels/addresses to backfill historical semantics without point-in-time proof.
