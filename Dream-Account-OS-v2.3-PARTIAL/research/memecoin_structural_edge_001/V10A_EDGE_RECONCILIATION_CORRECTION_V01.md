# MSEL-001 — V10A Edge Reconciliation Technical Correction V0.1

Status: TECHNICAL CORRECTION / PRE-OUTCOME / FAIL-CLOSED
Date: 2026-09-15
Branch: `memecoin-structural-edge-v0.1`

## Trigger

The first execution of `pilot/apply_holder_pit_clustering_v10.py` stopped fail-closed before writing clustering outputs with:

`V09_RESOLVED_EDGE_RECONCILIATION_FAILURE wallet=botcGXTCodVYmMyr59xtocrpMZzJ3AmwWa7nusQNyio`

No market outcome was opened and no clustering result was produced by that failed run.

## Root cause class

V0.9 explicitly retains every accepted direct inbound standard System Program Transfer found in the nearest qualifying funding transaction, and chooses the primary edge as the largest individual lamport transfer in that transaction.

V1.0 reconciliation then attempted to identify that primary edge by `(wallet, funding_signature, funder, lamports, instruction_class)` and required exactly one matching edge. If the same funding transaction contains two or more economically equivalent accepted transfers with the same funder and the same maximum lamport amount, the V0.9 status is economically unambiguous for the clustering fields but V1.0's instruction-level reconciliation can return multiple matches and fail.

This is a technical reconciliation mismatch between the V0.9 evidence representation and V1.0's uniqueness guard. It is not an outcome-driven feature change.

## Authorized correction

V10A changes only V0.9 final-edge reconciliation:

1. V0.5 reconciliation remains exactly as V1.0 implemented it.
2. A V0.9 final status still must be `DIRECT_FUNDING_EVIDENCE_FOUND_STANDARD_TRANSFER`.
3. Candidate edges still must match the frozen final primary signature, funder, lamports and `SYSTEM_TRANSFER` instruction class.
4. If exactly one candidate exists, behavior is unchanged.
5. If multiple candidates exist, they may be canonicalized to one edge only when all candidates are identical on the economically relevant tuple:
   - wallet;
   - funder;
   - lamports;
   - funding signature;
   - funding block time;
   - funding slot;
   - instruction class.
6. Differences only in instruction scope/index are allowed because those fields do not enter the frozen clustering policy.
7. If duplicate candidates disagree on any economically relevant field, V10A fails closed.
8. Deterministic canonical representative: sort by `(scope, instruction_index)` and select the first.

## Scientific invariants unchanged

- No funding lookback change.
- No new RPC.
- No new wallets.
- No threshold change.
- Degree policy unchanged.
- Tier A / Tier B synchronization rules unchanged.
- No high-degree hub auto-merge.
- No outcome access.
- No price access.
- No live trading.
- No merge to main.
- No post-outcome tuning.

The correction exists solely to make instruction-level duplicate representation compatible with the already-frozen V0.9 primary-funder semantics.
