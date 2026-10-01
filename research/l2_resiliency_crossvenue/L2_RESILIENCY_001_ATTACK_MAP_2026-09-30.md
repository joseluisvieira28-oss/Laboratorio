# L2-RESILIENCY-001 — ATTACK MAP — 2026-09-30

Purpose: prevent duplicate mining and preserve scientific distinctions.

| Line | Current state | Meaning | Reopen rule |
|---|---|---|---|
| L2-RESILIENCY-001 parent mechanism | VALIDATED | Replenishment mechanism replicated independently; informational effect exists. | Parent verdict immutable. |
| L2R-EXEC-TAKER-001 | CLOSED / ECONOMICALLY INFEASIBLE | Direct taker execution costs exceed observed parent effect. | New materially different execution route only. |
| L2R-EXEC-PASSIVE-001 | CLOSED | Even perfect-touch-fill upper bound is negative at documented Hyperliquid maker fee. | Separately frozen account-specific route with effective maker fee <= 0.4 bps/fill before outcomes. |
| L2R-EXEC-PASSIVE-FEETIER-001 | DORMANT | Required low-fee account condition not proven. | Objective pre-outcome fee proof <= 0.4 bps/fill. |
| L2R-OVERLAY-ETF-CME-001 | NO TERMINAL DIRECTIONAL RESULT | Original implementation was source/timing blocked; retries remained technical. | Do not claim support or no-edge from this identity. |
| L2R-OVERLAY-ETF-CME-SPAN-001 | CLOSED / DEVELOPMENT_SPAN_NO_SUPPORT | Aggregate panel positive but failed frozen robustness gates; R15 failed. | No rescue under same identity. |
| L2R-OVERLAY-ETF-CME-PRET0-001 | CLOSED / INSUFFICIENT_SAMPLE_OR_SOURCE | Frozen 1,100 ms causal PRET0 reference passes only 11/46 source pairs vs minimum 40. Directional outcomes were not opened. | No threshold widening under same identity. |
| L2R-CROSSVENUE-001 | SOURCE_TIMING_READY / PARENT_ANCHOR_BYTES_BLOCKED | Binance 2024 source + timestamp cadence preflight PASS; external lookup frozen at first aggTrade at/after target with 2,000 ms max lateness. Exact anchor ZIP is located in Library, but its raw bytes are not exportable to the current runtime. | Materialize the existing anchor ZIP/CSV and verify SHA be2c2d...37eb3. Do not open 2024 cross-venue outcomes before that byte check. |

## MEXC fee reconciliation

MEXC API fees do not satisfy the dormant L2 low-fee trigger and do not reopen the direct L2 execution children.

## Priority

Only one materially new L2 research path remains open without changing a failed rule:

**L2R-CROSSVENUE-001**

2026-10-01 update: Binance timestamp-only cadence gate PASS on 20/20 frozen 2024 dates (26,709,512 gaps); p99.9=1,947 ms; external lookup tolerance prospectively frozen to 2,000 ms. Parent anchor bytes remain the sole source blocker.

Do not spend additional research effort on direct Hyperliquid execution, SPAN, or PRET0 rescue unless a pre-existing frozen reopen condition is objectively satisfied.

2025 remains protected holdout for L2R-CROSSVENUE-001.
2026 remains forbidden for retrospective cross-venue discovery.

No main merge. No live trading.
