# OPTIONS-SPOTPERP-002 — PROMOTION POLICY V2 AUDIT

Status: TIER 2 — PROMOTED CANDIDATE
Operational label: QUASE DIAMANTE / NEAR-DIAMOND
Historical/parent result preserved: OPTIONS-SPOTPERP-001 = DISCOVERY_FAIL_NO_PROMOTION
Child Discovery classification preserved: OPTIONS-SPOTPERP-002 = CONTEXT_DEPENDENT

## Governing policy

Policy: CRYPTO NEAR-DIAMONDS RECOVERY PROGRAM — V2
Policy ID: ND-PROMOTION-POLICY-V2.0-FROZEN-2026-09-14
Drive policy revision existed at 2026-09-14T05:43:38.807Z, before the child Discovery execution opened outcomes at approximately 2026-09-14T06:36Z.

No V2 criterion was changed after the OPTIONS-SPOTPERP-002 outcome was observed.

## Canonical provenance

- Repository: joseluisvieira28-oss/Laboratorio
- Child branch: options-spotperp-regime-v0.2
- Child scientific HEAD at execution: 9db362c2f6d8167edb35c332e03bd79a095398a8
- Canonical monthly raw run: 34778911131
- Canonical final Source/Data Gate run: 34811277716
- Canonical child Discovery run: 34814162118
- Source/Data Gate: SOURCE_AUDIT_PASS
- 2025 accessed: NO
- 2026 accessed: NO
- Live trading authorized: NO
- Exchange mutation authorized: NO

## Prospectively frozen mechanism

The child experiment did not select winning calendar years after outcomes. It used only contemporaneously observable BTC regime variables frozen before execution:

- 30-day BTC trend: UP / DOWN
- 30-day realized volatility: HIGH / LOW
- Frozen volatility threshold: 80% annualized
- Four regimes: UP_HIGH, UP_LOW, DOWN_HIGH, DOWN_LOW

The regime assessed for Tier 2 is UP_LOW because the child Discovery produced it under this prospectively frozen partition. No threshold, horizon, asset, cost, year, or subgroup was altered after outcomes.

## UP_LOW canonical Discovery evidence

- Regime observations: n = 629
- Entered trades: 628
- beta = +0.0009068464863412072
- one-sided HAC p = 0.028352621881339246
- base cost = 10 bps
- gross mean = +18.603298315571585 bps/trade
- net mean = +8.603298315571585 bps/trade
- profit factor = 1.0904041717998876
- cumulative net return = +71.6499657218908%
- max drawdown = -58.93829791488026%
- positive major temporal blocks at base cost: 2 of 4 years = 50%
  - 2021: -44.65365353809316 bps/trade
  - 2022: +36.433942920334815 bps/trade
  - 2023: -19.891836270937198 bps/trade
  - 2024: +42.62204763309136 bps/trade
- single-year share of total positive gross PnL = 72.44201047640862%
- 20 bps stress net mean = -1.3967016844284132 bps/trade
- 20 bps stress PF = 0.9860715157618183

## TIER 2 hard-eligibility audit

A. Provenance clean and reproducible: PASS.

B. No leakage, hindsight, outcome-driven parameter selection or cherry-picking: PASS. Regime definitions and threshold were frozen before the child run.

C. Adequate sample under the frozen mechanism: PASS. n=629 exceeds the child minimum n>=120 and is not formally INSUFFICIENT_SAMPLE.

D. Base-cost economics non-negative: PASS. Net mean > 0 and PF >= 1.00 at frozen 10 bps base cost.

E. Expected relationship/sign correct: PASS. beta is positive in the pre-specified direction.

F. No fatal execution/risk pathology under Policy V2 automatic rule: PASS WITH FRAGILITY FLAG. Max drawdown exceeds 50%, but cumulative net is far above the <5% automatic Tier-2 block threshold. High drawdown remains a material risk flag.

G. Not solely a post-hoc selected asset/regime/quarter/horizon/subgroup: PASS. UP_LOW belongs to a complete four-regime partition frozen before outcomes.

## TIER 2 support path

Path 1 — Statistical: PASS.

- primary one-sided p <= 0.10: PASS (0.02835)
- at least 50% of major temporal blocks positive: PASS (2/4 = 50%)

Path 2 independent/OOS replication: NOT YET USED.
Path 3 portfolio: NOT USED.

## V2 verdict

TIER 2 — PROMOTED CANDIDATE.

This is the official near-diamond / quasi-diamond category for this implementation under frozen Promotion Policy V2. It is not TIER 1 VALIDATED EDGE and does not authorize live trading.

## Fragility flags retained

- high max drawdown (~58.9%)
- temporal unevenness (2/4 positive years)
- positive gross-PnL concentration in 2024 / single-year share ~72.4%
- 20 bps stress-cost economics slightly negative

These flags must be carried into any Confirmation/OOS design. They may not be hidden or tuned away.

## Next gate

The next scientific objective is independent/OOS Confirmation toward TIER 1 VALIDATED EDGE, using a prospectively frozen protocol. Do not open protected 2025 or 2026 data unless separately authorized by that protocol. No live trading, no exchange mutation, no merge to main, no parameter rescue.
