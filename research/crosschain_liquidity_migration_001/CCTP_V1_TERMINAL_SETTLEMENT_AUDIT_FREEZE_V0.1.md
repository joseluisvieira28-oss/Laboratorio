# CCLM V1 TERMINAL SETTLEMENT AUDIT V0.1

Frozen: 2026-09-24 after SOURCE_SMOKE_PARTIAL, before this audit is run.

Purpose: explain the 13 NO_RECEIVED_NONCE source gaps without changing the
original smoke result or any market hypothesis.

## Fixed cohort
Use every Avalanche->Ethereum native-USDC CCTP V1 source message from the
already frozen 2023-08-20 UTC source cohort. The observed cohort size is 16.

Do not select only successful or failed transfers.

## Destination search cutoff
Search Ethereum from the source boundary through:
2024-12-31T23:59:59Z

No 2025/2026 block or log may be requested.

## Canonical terminal completion
A source message is SETTLED_CANONICAL only if all are true:
1. exactly one Ethereum MessageReceived exists for the same sourceDomain=1 and nonce;
2. sender and message body exactly match the source MessageSent;
3. the same destination transaction contains exactly one MintAndWithdraw matching
   native Ethereum USDC, source amount and mint recipient.

Other statuses:
- NOT_RECEIVED_BY_CUTOFF
- RECEIVED_SEMANTIC_MISMATCH
- AMBIGUOUS_RECEIVED
- MINT_OR_AMOUNT_MISMATCH
- TECHNICAL_FAILURE

This is source-completeness adjudication only. It cannot alter the original
+2-day smoke classification and earns ZERO edge/promotion credit.
