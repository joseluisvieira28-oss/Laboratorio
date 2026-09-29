# SOURCE GATE V0.1 — CCLM-CCTP-USDC-001

Frozen: 2026-09-24

## Official semantics

Circle CCTP is permissionless and moves native USDC by burning on the source blockchain and minting on the destination blockchain.

The attestation API documentation states that a message hash is generated from the message bytes emitted by the MessageSent event and is used to retrieve the signed attestation for the source-chain burn event.

Current CCTP also distinguishes Fast Transfer and Standard Transfer. Those modes have different transfer-time semantics and must not be pooled blindly.

## Canonical transfer identity

Preferred immutable pairing key:
- CCTP message hash derived from canonical message bytes.

Every paired transfer must retain:
- message hash;
- protocol version if known;
- transfer mode if known (FAST / STANDARD / UNKNOWN);
- source chain/domain;
- destination chain/domain;
- burn transaction hash;
- burn block number and block timestamp;
- destination mint transaction hash;
- mint block number and block timestamp;
- USDC amount in atomic units;
- token contract identity on both chains;
- raw log/message hashes;
- collector/source version.

## Clock rule

Source-chain and destination-chain block timestamps are different clocks.
The lab MUST NOT interpret:
mint_block_ts - burn_block_ts
as a precise network transit latency without a sensitivity/chain-clock model.

The paired timestamps may be used for coarse lifecycle duration and ordering only until clock behavior is validated.

## V0.1 source questions

1. Can historical CCTP transfers be reconstructed from public chain logs with deterministic message-hash pairing?
2. Can amount, source/destination and protocol version be recovered without relying on a mutable third-party label database?
3. Can transfer-mode changes/version migrations be segmented without hindsight?
4. Is coverage complete enough by chain/day for a later directional-flow experiment?

## Initial chain scope

Do not freeze a broad chain universe before source inventory.
Source gate first proves at least two chains with:
- official CCTP support;
- public historical logs;
- deterministic pairing;
- >= 99% pair completeness within the chosen bounded pilot window.

The eventual Discovery chain universe must be frozen after this source census and before outcomes.

## Source verdict at open

SOURCE_PARTIAL.

Positive:
- official burn/mint mechanism exists;
- message-hash/attestation identity exists;
- onchain logs are in principle immutable.

Unproven:
- historical cross-chain pair completeness;
- version/mode coverage;
- free RPC/archive accessibility at required depth;
- cross-chain clock comparability.

## Fail-closed rules

- Unpaired burn != outflow completed.
- Unpaired mint != canonical CCTP inflow unless message identity is proven.
- Amount mismatch => transfer invalid for canonical flow.
- Current supported-chain list is not retroactively historical support.
- Fast and Standard modes cannot be pooled before mode semantics are preserved.
- Current CCTP v2 parsing cannot be silently applied to v1-era messages.
