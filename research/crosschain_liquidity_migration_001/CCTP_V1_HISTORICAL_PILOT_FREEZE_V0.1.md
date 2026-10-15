# CCTP V1 HISTORICAL PILOT FREEZE V0.1

Frozen: 2026-09-24
Lab: CROSSCHAIN-LIQUIDITY-MIGRATION-001
Child: CCLM-CCTP-USDC-001
Outcome access: CLOSED

## Why this pilot

Circle launched CCTP mainnet on 2023-04-26 for Ethereum and Avalanche.
Circle's V1 documentation states that CCTP V1 uses native burn-and-mint and supports Standard Transfer only.
Current Circle domain documentation maps:
- Ethereum = domain 0
- Avalanche = domain 1

This gives a pre-2025 source window without V2 Fast Transfer/Hooks ambiguity.

Official references:
- https://www.circle.com/pressroom/circle-delivers-usdc-interoperability-across-ecosystems-with-mainnet-launch-of-cross-chain-transfer-protocol
- https://developers.circle.com/cctp/v1
- https://developers.circle.com/cctp/concepts/supported-chains-and-domains

## Frozen source pilot

Protocol: CCTP V1 only
Asset: native USDC only
Routes:
- Ethereum -> Avalanche
- Avalanche -> Ethereum

Window:
- start: 2023-05-01T00:00:00Z
- end: 2024-12-31T23:59:59Z

Transfer mode:
- STANDARD only

## Source success gates

A canonical paired transfer requires:
1. source burn/message provenance;
2. deterministic message hash;
3. destination mint provenance;
4. exact amount match;
5. route/domain consistency;
6. no duplicate canonical message hash.

Pilot SOURCE_DATA_PASS requires:
- >= 99.0% of source burn/message records pair to one valid destination mint OR a documented protocol-valid terminal state;
- zero unresolved amount mismatches;
- zero unresolved duplicate message hashes;
- complete daily coverage of source-chain acquisition for every day after the first observed transfer in-window;
- raw source manifests and SHA-256 hashes;
- no access to 2025 or 2026 source blocks.

## Explicitly closed

- destination token/native-asset prices;
- BTC/ETH/AVAX returns;
- DEX volume/liquidity outcomes;
- CEX OI/funding;
- PnL;
- direction or threshold selection.

Passing this pilot proves only that directional CCTP V1 flow can be reconstructed.
