# L2-RESILIENCY-001 — EXECUTION FEE RECONCILIATION — 2026-09-30

Status: **NO REOPEN — MEXC API DOES NOT SATISFY THE FROZEN LOW-FEE TRIGGER**

Parent mechanism remains: VALIDATION_PASS.

Existing execution children remain:
- standard-base Hyperliquid taker: CLOSED;
- standard-base Hyperliquid passive maker: CLOSED;
- account-specific low-fee maker child: DORMANT unless effective maker fee <= 0.4 bps/fill before new outcome access.

## Why the recent fee correction does not reopen L2

The passive 2025 optimistic upper-bound study froze fee scenarios before its result:
- 0.0 bps/fill -> equal-weight mean net +1.330364 bps;
- 0.4 bps/fill -> +0.530364 bps;
- 0.8 bps/fill -> -0.269636 bps;
- 1.2 bps/fill -> -1.069636 bps;
- 1.5 bps/fill -> -1.669636 bps.

The frozen legitimate reopen trigger was therefore effective maker fee <= 0.4 bps/fill.

Current MEXC API Futures schedule effective 2026-06-01:
- maker 0.06% = 6 bps/fill;
- taker 0.08% = 8 bps/fill.

Operator-provided real MEXC fills audited in September 2026 were consistent with approximately 8 bps/fill on taker executions.

Therefore:
- MEXC API maker is 15x the frozen 0.4 bps maker trigger;
- MEXC API taker is 20x the frozen 0.4 bps maker trigger;
- maker+maker round trip is 12 bps before spread, queue/adverse-selection and latency;
- taker+taker round trip is approximately 16 bps before spread/slippage.

This does not reopen the L2 standalone execution children.

## Important interpretation

The fact that a small-notional trade pays only cents of fee does not mean its fee rate is small.

At zero fees the L2 passive diagnostic has positive gross/upper-bound potential, so the parent mechanism is not being declared NO_EDGE. But zero-fee perfect fills are not an executable route, and the prior study intentionally assumed unrealistically favorable 100% touch fills.

The next legitimate L2 route remains a materially new incremental overlay or a separately frozen lower-cost execution venue that proves its fee envelope before outcomes. Do not retroactively substitute MEXC for the closed Hyperliquid child.

No market outcomes were opened by this reconciliation.
