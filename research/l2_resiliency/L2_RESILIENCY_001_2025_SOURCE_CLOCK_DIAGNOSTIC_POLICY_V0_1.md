# L2-RESILIENCY-001 — 2025 SOURCE CLOCK SEMANTICS DIAGNOSTIC V0.1

Status: AUTHORIZED SOURCE-ONLY DIAGNOSTIC / HOLDOUT OUTCOMES STILL CLOSED

Purpose: determine whether the 2025 SOURCE_SCHEMA_FAIL_CLOSED on raw.data.time > envelope is isolated corruption, clock quantization, or a broader archive timestamp-semantic change.

Inputs:
- Exact 8,400 byte-verified official Hyperliquid BTC l2Book 2025 objects.
- Frozen manifest SHA256 3417647e5cc093a437d083eac4247df7c9bc6488ca9340aa44dc8a11b9a7906c.

Allowed measurements:
- top-level envelope timestamp partition membership and monotonicity;
- raw.data.time integer millisecond parsing;
- envelope_ns - payload_ms*1e6 lag distribution;
- full ledger of payload-after-envelope rows;
- size and temporal distribution of future-payload deltas;
- comparison against millisecond quantization boundaries;
- payload reversals/equality counts.

Forbidden:
- sweep construction;
- replenishment ratios;
- WEAK/STRONG labels;
- midpoint response/direction;
- returns/PnL/costs;
- 2026 access;
- any change to the frozen validation rule before this diagnostic is closed.

Routing:
- If violations are material/incoherent => keep validation BLOCKED_SOURCE_CLOCK_SEMANTICS.
- If a deterministic source-clock explanation is established, any normalization amendment must be separately frozen prospectively before reopening 2025 outcomes.