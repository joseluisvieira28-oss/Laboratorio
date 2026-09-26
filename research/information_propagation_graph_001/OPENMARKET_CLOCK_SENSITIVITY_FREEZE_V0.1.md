# OPENMARKET NEGATIVE CONTROL — CLOCK/OFFSET SENSITIVITY FREEZE V0.1

Frozen: 2026-09-24
Input corpus: exact v0.4.3-unified lag_pairs_ms
Revision: 74502466d1a7cef56395bfd8d0b465fbebc849cf

The exact lag reproduction already passed:
n=2,936,031; median=16 ms; p5=-186 ms; p95=316 ms.

## Frozen sensitivity grid

Apply deterministic constant source-clock offsets to lead_lag_ms:
-1000, -500, -250, -100, -50, 0, +50, +100, +250, +500, +1000 ms.

At each offset compute:
- median;
- p5 / p95;
- share lead_lag_ms > 0;
- share lead_lag_ms < 0.

No rows are dropped except non-finite values already excluded by the reproduction.

## Method-validation conditions

PASS if:
1. every shifted median equals base median + offset exactly within 1e-9;
2. both negative and positive direction interpretations occur somewhere inside
   the frozen +/-50/100/250/500/1000 ms grid;
3. the receipt explicitly classifies the apparent lead direction as
   CLOCK_OFFSET_SENSITIVE rather than as a causal latency estimate.

This is intentionally a negative control. Sensitivity is the expected outcome.
No predictive edge or candidate promotion can result from PASS.
