# STABLECOIN-EXCHANGE-FLOW-001 — FINAL DATA GATE CRITERIA V0.1

STATUS: FROZEN BEFORE FULL ACQUISITION RESULT AND BEFORE LATE-PERIOD CROSSCHECK RESULT

LAB: `STABLECOIN-EXCHANGE-FLOW-001`  
MVE: `SEF-BINANCE-PUBLIC-USDT-ETH-1D-001`

This document freezes the conditions required to release this source dataset to pre-Discovery protocol design. It does not authorize BTC price/outcome access.

## Mandatory gate conditions

The final source/data gate is `DATA_GATE_PASS` only if **all** conditions below pass.

### A. Source provenance

1. The already-observed 2022-11-11 independent MEV Blocker ↔ Blockchair comparison remains recorded as `SOURCE_CROSSCHECK_EXACT_PASS`.
2. The separately launched late protected comparison on **2024-11-11** must also classify `SOURCE_CROSSCHECK_EXACT_PASS` with exact equality in:
   - external inbound transfer count;
   - external outbound transfer count;
   - external inbound raw integer USDT value;
   - external outbound raw integer USDT value;
   after exclusion of frozen-basket internal sweeps.
3. If the 2024 cross-check mismatches in any required field, the final data gate FAILS CLOSED and BTC outcomes remain prohibited. No tolerance band is allowed.

### B. Protected dataset coverage

4. Full acquisition receipt must classify `DATA_ACQUISITION_PASS`.
5. CSV must contain exactly **781** daily rows.
6. First row date must be exactly `2022-11-11` UTC.
7. Last row date must be exactly `2024-12-30` UTC.
8. Dates must be unique, strictly increasing, and contain every calendar day in the closed interval with zero missing dates. Zero-flow days must exist as explicit rows.
9. No row dated 2025 or 2026 is permitted.

### C. Deterministic arithmetic / schema

10. Required columns must be present exactly as defined by `DATA_ACQUISITION_PROTOCOL_V0.1.md`:
    - date_utc
    - external_in_count
    - external_out_count
    - external_in_raw
    - external_out_raw
    - net_flow_raw
    - external_in_usdt
    - external_out_usdt
    - net_flow_usdt
    - first_block
    - last_block
11. Counts and raw amounts must be non-negative integers except `net_flow_raw`, which may be signed.
12. Every row must satisfy exactly:
    - `net_flow_raw = external_in_raw - external_out_raw`;
    - `external_in_usdt = external_in_raw / 1,000,000`;
    - `external_out_usdt = external_out_raw / 1,000,000`;
    - `net_flow_usdt = net_flow_raw / 1,000,000`.
13. No clipping, winsorization, z-score, threshold, percentile, normalization or market-price-derived feature is allowed in the canonical source CSV.

### D. Extraction integrity

14. Manifest must identify the frozen nine-address basket, Ethereum USDT contract, MEV Blocker endpoint, protected dates, repository commit and 3,200-block base chunk policy.
15. Manifest must contain a query receipt for every successful base/adaptively split source query, including block range, direction, result count and response hash/bytes.
16. The acquisition implementation must have failed closed on any unresolved range, malformed log, missing/malformed `blockTimestamp`, disagreeing duplicate, removed log, illegal timestamp, or protected-period crossing. A final PASS therefore requires no unresolved such condition.
17. Global protected block-boundary proofs must show acquisition begins at/after `2022-11-11 00:00:00 UTC` and terminates before `2024-12-31 00:00:00 UTC` without querying/accepting 2025 data.
18. Receipt flags must be exactly:
    - `access_2025=false`
    - `access_2026=false`
    - `btc_market_data_accessed=false`
    - `returns_computed=false`
    - `pnl_computed=false`

### E. Immutable evidence

19. Canonical CSV SHA256 and extraction-manifest SHA256 must be recorded in the acquisition receipt.
20. The completed acquisition artifact must be archived outside the ephemeral runner (Drive preferred) before any BTC outcome is opened.
21. The final human-readable `DATA_GATE_DECISION` must cite both source cross-checks, acquisition receipt, immutable hashes and external archive location.

## Failure routing

- Failed source equality → `SOURCE_PROVENANCE_FAILURE` / no BTC outcomes.
- Missing/incomplete/corrupt rows → `DATA_FAILURE` / no BTC outcomes.
- Runner/API/transport failure before a complete receipt → `TECHNICAL_FAILURE_PREOUTCOME` / may be retried with source-only implementation remediation that does not alter scientific semantics.
- None of these classifications are `NO_EDGE`.

## What PASS authorizes

`DATA_GATE_PASS` authorizes only the next prospective step: design and freeze a separate BTC pre-Discovery protocol with fixed information transform, timing, primary horizon, statistical test, costs and promotion gates.

`DATA_GATE_PASS` does **not** by itself authorize BTC price download, return calculation, PnL, 2025/2026 access, live trading, exchange mutation, main merge or deployment.
