# CCTP V1 CONTRACT PROVENANCE CROSS-CHECK V0.1

Date: 2026-09-24
Lab: CROSSCHAIN-LIQUIDITY-MIGRATION-001 / CCLM-CCTP-USDC-001
Scope: Ethereum <-> Avalanche, CCTP V1, source-only

## Pinned V1 contracts

Ethereum / domain 0
- TokenMessenger: 0xBd3fa81B58Ba92a82136038B25aDec7066af3155
- MessageTransmitter: 0x0a992d191DEeC32aFe36203Ad87D7d289a738F81
- native USDC: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

Avalanche / domain 1
- TokenMessenger: 0x6B25532e1060CE10cc3B0A99e5683b91BFDe6982
- MessageTransmitter: 0x8186359aF5F57FbB40c6b14A588d2A59C0C29880
- native USDC: 0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E

## Evidence standard

The pin is accepted as CROSSCHECK_PASS, not as a claim that a current Circle
deployment table preserves a historical V1 address list.

Evidence is triangulated from:
1. Circle's verified GitHub organization and official evm-cctp-contracts repo,
   which preserves the V1 TokenMessenger / MessageTransmitter contract code and
   deployment mechanism.
2. Public chain explorer decoded events identifying the addresses as Circle
   CCTP v1 contracts.
3. The CCTP V1 message itself: Ethereum MessageSent payloads encode the
   destination TokenMessenger 0x6B255... for Avalanche, while Avalanche
   DepositForBurn/MessageSent logs originate from that same V1 TokenMessenger
   and its MessageTransmitter 0x818635....
4. Ethereum 2024 onchain transactions exist against 0xBd3f... as CCTP v1,
   proving the address was active inside the frozen historical window.

External evidence consulted:
- https://github.com/circlefin/evm-cctp-contracts
- https://github.com/circlefin/evm-cctp-contracts/blob/master/src/TokenMessenger.sol
- https://routescan.io/
- https://snowtrace.io/

## Gate decision

V1_CONTRACT_ADDRESS_PIN = PASS_CROSSCHECKED

This clears the prior address-provenance blocker for a bounded source
acquisition. It does NOT prove:
- complete historical log coverage;
- >=99% burn/mint pairing;
- archive RPC availability;
- economic edge.

Those remain the next source/data gates.

## Protected-period firewall

Acquisition code must enforce block timestamps <= 2024-12-31T23:59:59Z.
No 2025/2026 blocks may be persisted by the canonical pilot.
