# V0.1 LATENCY-BUCKET N CLARIFICATION
Date: 2026-10-05
Status: FROZEN BEFORE 2025 SUB-MINUTE PRICE OUTCOMES

For ACTIONABLE_WINDOW_CANDIDATE and COST_ROBUST_50BPS tests at a latency bucket:

- source-valid sample size is fixed at 8;
- that latency bucket must itself have valid_n = 8;
- NULL entry observations do not count as successes and cannot reduce the denominator to manufacture a pass.

All other frozen rules remain unchanged.
2026 remains unopened.
