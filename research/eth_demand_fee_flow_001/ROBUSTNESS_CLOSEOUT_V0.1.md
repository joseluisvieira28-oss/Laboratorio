# ETH-DEMAND-FEE-FLOW-001 — INFERENCE ROBUSTNESS CLOSEOUT V0.1

Date: 2026-09-20
Canonical robustness run: `35476547168`
Audit: `EDFF-FD45-INFERENCE-ROBUSTNESS-001`

## Parent status

The parent MVE remains **REPLICATION_MIXED**. This post-result audit was explicitly non-promotional and cannot upgrade, rescue or rewrite that verdict.

## Robustness result

**ROBUSTNESS_WEAK_NOT_PROMOTIONAL**

Exact parent 2024 sample:
- N = 248
- observed beta = +0.179882

45-day circular moving-block bootstrap:
- 10,000 replications
- beta 95% CI = [-0.167705, +0.514874]
- fraction beta > 0 = 82.91%

Circular-shift null:
- 159 admissible shifts
- two-sided p = 0.48125
- null beta 2.5% = -0.357140
- null beta 97.5% = +0.188080

Descriptive quarter slopes:
- 2024Q1 partial = +0.695240
- 2024Q2 = -0.075221
- 2024Q3 = +0.239970
- 2024Q4 partial = +0.433666

## Interpretation

The positive 2024 point estimate is not robust enough under dependence-preserving inference to claim a replicated predictive edge. The block-bootstrap interval crosses zero and the circular-shift null does not reject chance alignment.

The result remains scientifically interesting because the post-Dencun primary beta is positive, both frozen secondary horizon betas are positive, the 2023 placebo beta is negative/insignificant, and the 2024 primary R² is sizable. None of those facts override the frozen inference gate.

No thresholds, signal definition, horizon, alignment or sign were changed. No 2025/2026 outcome, PnL, live trading, wallet access, exchange mutation or merge to main was opened.
