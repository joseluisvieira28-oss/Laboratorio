# ARQ-001-MTF-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-23
Classification: **DISCOVERY_FAIL_NO_PROMOTION**

## Result

The 2024 Discovery failed the frozen promotion contract.

- Baseline A observations: 516
- Full D-confirmed observations: 85
- D-rejected baseline observations: 431
- D-confirmed BASE12 pooled mean: -15.9144 bps
- D-confirmed STRESS14 pooled mean: -17.9144 bps
- D-rejected BASE12 pooled mean: -14.7861 bps
- Incremental D-confirmed minus D-rejected: -1.1283 bps
- UTC-day bootstrap 95% interval for D-confirmed BASE12 mean: approximately [-57.27, +34.63] bps
- Positive ALT means at BASE12: 2 / 5
- ALTs with >=20 D-confirmed observations: 0 / 5
- Best-1% removal mean: -22.8523 bps
- Best-ALT removal mean: -24.1694 bps

Every economic/robustness promotion gate failed; source/provenance passed.

## Per-ALT D-confirmed BASE12

- ETHUSDT: n=17, +17.1055 bps
- SOLUSDT: n=18, -10.2462 bps
- BNBUSDT: n=19, +2.0075 bps
- XRPUSDT: n=15, -42.8217 bps
- DOGEUSDT: n=16, -53.4315 bps

These are diagnostics only and may not be cherry-picked into a rescue hypothesis.

## Firewall

2025 Confirmation was NOT opened.
2026 final holdout was NOT opened.
No live trading, order, exchange mutation, wallet action or main merge occurred.

## Decision

Close exact ARQ-001-MTF-001.

Do not:
- open 2025;
- invert the regime;
- change 4H/1H clocks;
- relax thresholds;
- select ETH/BNB only;
- change costs or horizon;
- tune on 2024;
- relabel this as edge.

The original ARQ-001-DRF-001 remains independently SOURCE_BLOCKED at 1m. This sibling experiment answers the 4H-regime/1H-follower formulation only.
