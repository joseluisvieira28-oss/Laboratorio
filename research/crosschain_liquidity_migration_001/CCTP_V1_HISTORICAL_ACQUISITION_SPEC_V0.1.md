# CCTP V1 HISTORICAL ACQUISITION SPEC V0.1

Frozen: 2026-09-24
Pilot window and routes are inherited from CCTP_V1_HISTORICAL_PILOT_FREEZE_V0.1.

## Canonical contracts

Ethereum:
- MessageTransmitter 0x0a992d191deec32afe36203ad87d7d289a738f81
- TokenMessenger 0xbd3fa81b58ba92a82136038b25adec7066af3155

Avalanche:
- MessageTransmitter 0x8186359af5f57fbb40c6b14a588d2a59c0c29880
- TokenMessenger 0x6b25532e1060ce10cc3b0a99e5683b91bfde6982

## Required logs

Source chain:
- MessageTransmitter.MessageSent(bytes)
- TokenMessenger.DepositForBurn(...) as cross-check, not primary pairing authority.

Destination chain:
- MessageTransmitter.MessageReceived(...)
- TokenMessenger.MintAndWithdraw(...)

## Pairing

Primary lifecycle key:
(sourceDomain, nonce)

For every source MessageSent:
1. decode exact official V1 message layout;
2. require source/destination domains in frozen {0,1} route;
3. require message version=0 and burn-body version=0;
4. retain raw message bytes and source tx/block provenance;
5. locate exactly one destination MessageReceived with same sourceDomain+nonce;
6. require destination body and sender to match source message semantics;
7. require a MintAndWithdraw in the same destination transaction;
8. require exact amount equality.

Replacement-message case:
TokenMessenger V1 permits replacement using the same nonce before one message confirms. Therefore more than one source MessageSent for one sourceDomain+nonce is NOT silently deduplicated. The confirmed destination MessageReceived must select the exact body that landed; unresolved ambiguity blocks that lifecycle.

## Transport gate

Historical acquisition may use a public RPC only if:
- eth_getLogs returns deterministic bounded ranges;
- block-by-number is available across the full pilot window;
- provider limitations/errors are recorded;
- raw responses or normalized log rows are hashed;
- no range is silently truncated.

Ethereum and Avalanche transports are source plumbing, not scientific authority; contract/event semantics come from Circle.

## No-outcome firewall

Forbidden in this stage:
- AVAX/ETH/BTC prices;
- CEX/DEX volume/liquidity;
- funding/OI;
- forward returns;
- PnL.

## Verdicts

SOURCE_DATA_PASS
SOURCE_PARTIAL
SOURCE_ACCESS_BLOCKED
PROVENANCE_FAILURE
TECHNICAL_FAILURE

Never NO_EDGE at this stage.
