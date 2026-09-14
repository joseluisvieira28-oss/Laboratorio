# STABLECOIN-EXCHANGE-FLOW-001 — PRE-DISCOVERY TECHNICAL AMENDMENT 002

STATUS: **FROZEN PRE-OUTCOME / EVIDENCE-CHAIN CLARIFICATION ONLY**

This amendment is frozen before any BTC outcome candle is accessed.

It changes no hypothesis, signal, address basket, eligible date, direction, timing, horizon, cost, bootstrap rule, threshold, or promotion gate.

## Immutable evidence chain

The original full source build is GitHub Actions run `34896944142`.

That build successfully produced the complete protected source corpus:

- 780 UTC boundary rows;
- 779 net-flow signal rows;
- boundary invariants PASS;
- date integrity PASS;
- net-flow arithmetic PASS;
- no BTC market data accessed;
- no 2025 or 2026 access.

Its original receipt remains permanently classified `DATA_FAILURE` because the independently fixed MEV Blocker QA subset completed only 220/243 individual calls after HTTP 429 rate limiting. The original receipt must not be rewritten.

A pre-outcome QA-transport remediation was then run as GitHub Actions run `34897999268`, using the already pre-probed nine-call MEV Blocker JSON-RPC batch transport on the **exact same prospectively fixed 27 QA dates** and the exact same nine addresses.

The remediation result is `SOURCE_DATASET_PASS`:

- 27/27 batches completed;
- 243/243 logical QA balances completed;
- 243/243 exact matches against the immutable dRPC source balances;
- zero transport errors;
- zero value mismatches;
- source CSV hash and original receipt hash verified;
- no BTC market data accessed;
- no 2025 or 2026 access.

## Discovery authorization rule

The frozen Discovery runner may consume the original source CSV from run `34896944142` **only if** it also consumes and validates the separate remediation receipt from run `34897999268` and proves the two artifacts are cryptographically chained through:

1. the original source CSV SHA256;
2. the original source receipt SHA256;
3. original source run ID `34896944142`;
4. remediation classification `SOURCE_DATASET_PASS`;
5. `qa_exact_match_pass == true`;
6. `qa_error_count == 0`;
7. `qa_mismatch_count == 0`;
8. `qa_calls_logical_completed == 243`.

This amendment does not erase or reclassify the original failed QA attempt. It records a separate technical remediation completed while outcomes remained closed.
