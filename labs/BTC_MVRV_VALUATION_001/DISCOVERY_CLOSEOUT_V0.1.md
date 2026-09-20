# BTC-MVRV-VALUATION-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35499557287`
MVE: `BMV-30D-VALUATION-001`

## Verdict

**DISCOVERY_FAIL_NO_PROMOTION**

Only the frozen 2019-2023 Discovery outcomes were opened. The conditional 2024-2025 holdout remained closed.

Discovery:
- N = 1,826 daily signal dates
- beta on ln(MVRV) = -0.03288
- HAC t = -0.531
- HAC p = 0.595
- R² = 0.346%
- lowest-minus-highest MVRV quintile 30d return spread = +1.084 percentage points

Passed:
- N >= 1,500
- beta < 0
- low-minus-high quintile spread > 0

Failed:
- HAC t <= -2
- R² >= 1%
- positive annual quintile spread in >=3 years

The direction is consistent with the economic hypothesis, but the effect is weak and unstable under the frozen 30-day specification. No 2024-2025 holdout was opened and no alternate horizon, MVRV variant, cycle filter, or 2026 rescue is authorized.

No PnL, live trading, exchange mutation, wallet access or merge to main occurred.
