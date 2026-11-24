# LIDO-WITHDRAWAL-QUEUE-PRESSURE-001 — PROSPECTIVE SOURCE FREEZE V0.1

Status: NEW_ID / SOURCE-ONLY / PROSPECTIVE EVIDENCE REQUIRED
Primary family: FLOW
Secondary family: SUPPLY / MR

## Mechanism

The observable is the **aggregate state of Lido's withdrawal queue**:
- new stETH/wstETH withdrawal requests;
- outstanding queue inventory;
- finalization throughput;
- queue-age / backlog pressure.

This is not STETH-REDEMPTION-BASIS-002's one-position hypothetical redemption trade.

## Contamination map

STETH-REDEMPTION-BASIS-002 already used 2023-05-16 through 2024-12-31 and opened its economic Discovery. It ended DISCOVERY_INSUFFICIENT_SAMPLE with 2 completed non-overlapping redemptions vs minimum 30.

Therefore:
- that period cannot be presented as pristine confirmation for this new queue-pressure hypothesis;
- this new ID inherits zero promotion credit;
- no 2023-2024 market-response computation is authorized here;
- fresh prospective evidence is required before a scientific edge claim.

## Source authority

Official Lido WithdrawalQueueERC721 documentation:
https://docs.lido.fi/contracts/withdrawal-queue-erc721/

Canonical queue contract from prior Crypto Lab source authority:
0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1

Source-only probe may verify:
- bytecode;
- historical eth_getLogs accessibility after canonical queue activation;
- WithdrawalRequested / WithdrawalsFinalized schema availability.

## Future scientific contract

Not frozen yet:
- queue-pressure threshold;
- response asset;
- direction;
- horizon;
- economic translation.

Those fields must remain UNKNOWN until a separate pre-outcome freeze using fresh evidence.

## Failure classes

SOURCE_PASS_PROSPECTIVE_ONLY
SOURCE_BLOCKED
PROVENANCE_FAILURE
TECHNICAL_FAILURE

NO_EDGE is impossible at this stage.
