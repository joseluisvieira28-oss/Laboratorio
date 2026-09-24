# CCTP V1 CONTRACT PIN RECEIPT V0.1

Date: 2026-09-24
Lab: CROSSCHAIN-LIQUIDITY-MIGRATION-001
Child: CCLM-CCTP-USDC-001
Verdict: V1_CONTRACT_ADDRESS_AUTHORITATIVE_PIN_PASS

## Circle-owned authority

Circle's published USDCKit/CCTP chain definitions currently expose the CCTP V1 contract addresses used by the Ethereum and Avalanche integrations.

### Ethereum mainnet / domain 0
- MessageTransmitter: 0x0a992d191deec32afe36203ad87d7d289a738f81
- TokenMessenger: 0xbd3fa81b58ba92a82136038b25adec7066af3155

### Avalanche C-Chain / domain 1
- MessageTransmitter: 0x8186359af5f57fbb40c6b14a588d2a59c0c29880
- TokenMessenger: 0x6b25532e1060ce10cc3b0a99e5683b91bfde6982

Authority surface:
https://docs-w3s-node-sdk.circle.com/variables/providers_cross-chain-transfer-protocol.SUPPORTED_CHAINS.html

Circle's official evm-cctp-contracts repository is the canonical ABI/message-format authority:
https://github.com/circlefin/evm-cctp-contracts

## Source-code semantics frozen

Official V1 source defines:
- MessageTransmitter.MessageSent(bytes message)
- MessageTransmitter.MessageReceived(address caller,uint32 sourceDomain,uint64 nonce,bytes32 sender,bytes messageBody)
- TokenMessenger.DepositForBurn(...)
- TokenMessenger.MintAndWithdraw(...)
- Message layout: version[0:4], sourceDomain[4:8], destinationDomain[8:12], nonce[12:20], sender[20:52], recipient[52:84], destinationCaller[84:116], messageBody[116:]
- BurnMessage layout: version[0:4], burnToken[4:36], mintRecipient[36:68], amount[68:100], messageSender[100:132]

## Pair identity

Canonical V1 lifecycle identity for the pilot is:
(sourceDomain, nonce)

Additional integrity:
- full source message bytes retained;
- Keccak-256 message hash when implementation library is available;
- source destinationDomain must match frozen route;
- body amount must agree with destination MintAndWithdraw amount;
- MessageReceived sourceDomain/nonce/sender/body must agree with source message.

Why (sourceDomain, nonce) is acceptable:
MessageTransmitter V1 reserves a unique nonce on the source domain and destination receive protection tracks sourceDomain+nonce. Message hash remains an additional immutable payload identity.

## Consequence

The earlier blocker V1_CONTRACT_ADDRESS_AUTHORITATIVE_PIN_PENDING is CLOSED/PASS.
Historical data acquisition itself is not yet SOURCE_DATA_PASS.
