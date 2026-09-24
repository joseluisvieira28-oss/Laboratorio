# CCLM-002 2024-03/04 SEMANTIC MISMATCH DIAGNOSTIC FREEZE V0.1

Frozen: 2026-09-24
Stage: SOURCE SEMANTICS ONLY
Market outcomes: CLOSED

## Trigger

Full monthly source scale reconstructed 7,393 canonical settled flows but found
exactly four semantic mismatches:
- 2024-03 Ethereum -> Avalanche: 2
- 2024-04 Ethereum -> Avalanche: 2

All other months/routes had zero semantic mismatch.

The canonical completed-flow rule is NOT changed.

## Fixed diagnostic cohort

Every Avalanche MessageReceived during March and April 2024 satisfying:
- sourceDomain = Ethereum domain 0;
- sender = pinned Ethereum V1 TokenMessenger;
- V1 burn-body version = 0;
- burnToken = pinned Ethereum native USDC;
- no exact same-transaction MintAndWithdraw match under the existing rule.

Do not select or drop cases by amount, wallet, market behavior or outcome.

## Diagnostic reason codes

For each fixed case record:
- NO_MINT_EVENT_IN_TX
- DEST_TOKEN_MISMATCH
- AMOUNT_MISMATCH
- RECIPIENT_MISMATCH
- MULTIPLE_EXACT_MATCHES
- COMBINATION_MISMATCH
- DECODER_FAILURE

Retain transaction hash, nonce, source amount, hashes of raw evidence, and
candidate mint event fields required for source adjudication.

## Decision

PARSER_OR_BATCHING_CONFIRMED:
a deterministic source-encoding/batching explanation resolves all four without
changing the economic definition.

PROTOCOL_NONCANONICAL_CONFIRMED:
events are valid CCTP receives but do not satisfy completed native-USDC
settlement semantics. They remain excluded.

SOURCE_SEMANTICS_UNRESOLVED:
any case remains unexplained.

No result may change threshold, target, historical window or market outcome.
