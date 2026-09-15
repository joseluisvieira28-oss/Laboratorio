# MSEL-001 — Holder Funding Completeness Escalation Freeze V0.1

Status: RESEARCH-ONLY / FAIL-CLOSED / OUTCOMES LOCKED
Date: 2026-09-15
Branch: `memecoin-structural-edge-v0.1`

## Why this freeze exists

The V0.8 holder-universe audit was run before outcomes and showed that the V0.5 bounded funding search (12 prior signatures per wallet) leaves material unresolved funding exposure in the holder universe. This is a source-completeness issue, not an outcome-driven signal rescue.

The lab therefore permits exactly one deterministic funding-evidence escalation before any market outcome is opened.

## Frozen escalation rule

1. Universe: every external holder owner present in the frozen T+1/T+3/T+5 holder snapshots that is either:
   - absent from the V0.5 funding universe; or
   - `UNRESOLVED_WITHIN_BOUNDED_LOOKBACK` in V0.5; or
   - resolved in V0.5 only through an instruction class that is not independently trusted for this stage.
2. Existing V0.5 resolved evidence is accepted only when the chosen primary inbound edge is a standard Solana System Program `Transfer` (enum variant 2 / `SYSTEM_TRANSFER`).
3. `TransferWithSeed` is not used for new or carried primary funding evidence in this completion pass because its binary layout has not been separately frozen and verified for this lab. Any V0.5 primary evidence relying on that instruction class must be re-resolved under the standard-transfer-only rule.
4. Maximum search depth is frozen at **50 immediately-prior signatures per targeted wallet**.
5. For wallets already anchored by V0.5, use the existing point-in-time anchor and query signatures strictly before that anchor.
6. For a holder-only wallet absent from V0.5, derive the earliest positive target-token balance-change transaction as an anchor candidate. Use it only if that transaction is address-indexed for the wallet. If it is not address-indexed, mark the wallet unresolved; do not browse later wallet history to manufacture an anchor.
7. Only successful transactions strictly before the point-in-time anchor may contribute funding evidence.
8. Accepted funding evidence is direct inbound native SOL via standard System Program `Transfer` only.
9. The nearest prior transaction containing accepted direct inbound evidence defines the primary funder; if multiple inbound transfers occur in that same transaction, retain all and choose the largest lamport transfer as primary.
10. Absence of accepted funding evidence after this escalation does **not** mean the wallet is independent.

## Stop rule

After this 50-signature completion pass, the funding lookback may not be increased again because of observed coverage, clustering, or later outcomes. Remaining unresolved wallets must be carried as uncertainty into the final feature layer or cause the affected feature to remain bounded/unavailable.

## Governance

- No prices.
- No graduation status.
- No +15m/+1h/+6h/+24h token outcomes.
- No live trading.
- No exchange mutation.
- No merge to main.
- No post-outcome tuning.
- No hard cluster merges in the collector itself.
- The previously frozen hub/cluster policy remains unchanged.

This freeze is written before the completion collector is executed and before any MSEL market outcome is opened.
