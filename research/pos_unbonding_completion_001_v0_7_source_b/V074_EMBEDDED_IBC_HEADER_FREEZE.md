# V0.7.4 EMBEDDED IBC HEADER RECONSTRUCTION FREEZE

Date: 2026-10-07
Parent V0.7.2 amendment: 2857e56e85555fcd6356e2264f4687f6cd81b416
Parent V0.7.3 amendment: f7bc1e49f95c95765299f92137be434357f3cc81
Market outcomes opened: NO
Coreum unbonding/completion event counts opened: NO
Embedded IBC header fields decoded before this freeze: NO

## Purpose

Use the successful Coreum client-update transactions already deterministically selected by V0.7.2 as an independent, cryptographically verified Source-B reconstruction.

The canonical Osmosis transaction event contains a protobuf Any with type:
`/ibc.lightclients.tendermint.v1.Header`.

The embedded IBC Tendermint Header includes:
- SignedHeader;
- ValidatorSet;
- TrustedHeight;
- TrustedValidators.

The SignedHeader in turn includes the counterparty Tendermint block Header and Commit.

## Frozen checkpoints

Use exactly the two V0.7.2 deterministic first-update checkpoints already selected:
1. first qualifying update after 2023-07-01 UTC:
   - Osmosis host height 10,925,251
   - Coreum consensus height 7,022,341
2. first qualifying update after 2024-01-01 UTC:
   - Osmosis host height 13,034,470
   - Coreum consensus height 13,971,265

No replacement checkpoint may be chosen based on decoded values.

## Required proof per checkpoint

From the canonical successful Osmosis transaction result:
1. require tx result code = 0;
2. require update_client.client_id = 07-tendermint-2929;
3. require event consensus_height equals decoded SignedHeader.Header.height;
4. require decoded Header.chain_id = coreum-mainnet-1;
5. require decoded Header.time exactly equals Source-A Coreum block time;
6. require decoded Header.app_hash exactly equals Source-A Coreum app_hash;
7. require decoded SignedHeader.Commit.block_id.hash exactly equals Source-A Coreum block hash;
8. preserve SHA-256 of raw embedded Any bytes and the Osmosis host block hash.

Both frozen checkpoints must pass all eight requirements.

## Scientific interpretation

A successful IBC client update means the counterparty header was accepted by Osmosis' IBC Tendermint light client under Osmosis consensus. This evidence originates in canonical Osmosis history, not in TX/Coreum infrastructure.

If both frozen checkpoints pass, V0.7 may mark:
`COREUM_CRYPTOGRAPHIC_SOURCE_B_PASS`.

This proves independent historical consensus verification across separated dates. It does NOT by itself prove full unbonding census completeness. A separate pre-census freeze is still required before opening Coreum completion counts.

No market outcomes or unbonding counts may be read in this step.
