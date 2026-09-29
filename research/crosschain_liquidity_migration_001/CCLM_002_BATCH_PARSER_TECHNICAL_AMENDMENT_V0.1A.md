# CCLM-002 BATCH PARSER TECHNICAL AMENDMENT V0.1A

Date: 2026-09-25
Science change: NONE
Outcome access: CLOSED

## Trigger

The frozen 20-month source scale produced four apparent semantic mismatches,
all in two Avalanche destination transactions. The diagnostic showed multiple
exact MintAndWithdraw events with identical token / recipient / amount in the
same transaction.

The separately frozen batch-order adjudication proved all four messages pair
cleanly when transaction log order is preserved.

## Protocol authority

Circle CCTP V1 source code establishes the destination event order:

MessageTransmitter.receiveMessage()
1. invokes recipient TokenMessenger.handleReceiveMessage(...);
2. TokenMessenger mints and emits MintAndWithdraw;
3. only after the handler returns does MessageTransmitter emit MessageReceived.

Therefore, for one receiveMessage call, the corresponding MintAndWithdraw is
necessarily before its MessageReceived in transaction log order.

In a transaction batching multiple receiveMessage calls, pairing by
(token, recipient, amount) alone is insufficient when two equal transfers are
batched.

## Technical correction

Canonical event semantics are unchanged.

For each qualifying MessageReceived:
- restrict to exact token / recipient / amount MintAndWithdraw candidates in
  the same transaction;
- require mint logIndex < MessageReceived logIndex;
- require mint not already assigned;
- choose the nearest preceding exact unmatched mint.

This is deterministic transaction-order reconstruction of the existing
canonical event, not a new economic rule.

## Re-run requirement

All 20 frozen months, 2023-05 through 2024-12, must be re-run under the corrected
parser. The previous blocked receipt is preserved.

Only a new aggregate with:
- all 20 months present;
- zero technical failures;
- zero unresolved semantic mismatches;
may classify FULL_HISTORICAL_SETTLED_FLOW_SOURCE_PASS.

No market outcome, PnL, threshold, date split or predictor may change.
