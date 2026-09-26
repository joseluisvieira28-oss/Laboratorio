# CCLM-002 BATCH ORDER ADJUDICATION FREEZE V0.1

Frozen: 2026-09-24
Stage: SOURCE PARSER ADJUDICATION
Outcomes: CLOSED

## Fixed transactions

Derived from the already frozen four-case mismatch cohort:
- 0x634bb8aa7cc276dd5b40b7d03bcb18de1763faf9f7cf13bb778b00ce4c2318d1
- 0xb7b9fef5c25a37b47ac136105dae3f319a21475f35a02d4dd713d42c55867d8e

No other transaction may enter this adjudication.

## Official protocol ordering

Pinned Circle CCTP V1 source establishes:
1. MessageTransmitter.receiveMessage calls recipient handleReceiveMessage.
2. TokenMessenger.handleReceiveMessage calls _mintAndWithdraw.
3. _mintAndWithdraw emits MintAndWithdraw.
4. control returns to MessageTransmitter.
5. MessageTransmitter then emits MessageReceived.

Therefore, for successful batched receiveMessage calls inside one transaction,
the relevant protocol order is MintAndWithdraw before its corresponding
MessageReceived.

## PASS rule

BATCHING_PARSER_BUG_CONFIRMED only if, for each of the four fixed messages:
- one exact native-USDC MintAndWithdraw with matching recipient/amount occurs
  after the previous relevant MessageReceived (or tx start) and immediately
  before the message's MessageReceived among relevant CCTP Mint/Received events;
- the four source nonces are each assigned one-to-one to a distinct mint log.

Otherwise:
BATCH_PAIRING_UNRESOLVED.

No source or market rule may be changed by the diagnostic itself.
