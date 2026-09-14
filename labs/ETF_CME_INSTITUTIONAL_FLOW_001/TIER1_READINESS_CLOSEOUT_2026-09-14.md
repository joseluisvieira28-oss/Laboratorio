# ETF-CME-INSTFLOW-001 — TIER 1 READINESS CLOSEOUT — 2026-09-14

Status: `READINESS_FAIL` / Tier 2 unchanged.

Parent status: `TIER 2 — PROMOTED CANDIDATE — FRAGILE`.

GitHub Actions run: `34842535727`.
Artifact ID: `10346901735`.
Artifact SHA256: `c6805f95b05042a88eaefcee11512c1c52a896bc95d8e3a47abe7e7cabeec4cc`.

This was a prospectively frozen post-OOS execution/risk diagnostic using only the immutable 2025 OOS ledger. No new market outcomes were opened. Calendar 2026 remained unopened. This study cannot itself promote to Tier 1.

## Frozen readiness result

Passed 9 of 10 diagnostics. Failed only:

- leave-one-trade-out minimum base-net mean > 0: **FAIL**
- observed minimum LOO mean: `-0.0012068769794294043` (~`-12.07 bps/trade`)

Other key results:

- observations: `50`
- base net mean: `0.0011402860423247276` (~`+11.40 bps/trade`)
- base PF: `1.05719617081492`
- stress20 net mean: `0.00016028604232472696` (~`+1.60 bps/trade`)
- stress20 PF: `1.007836349329625`
- additive cumulative base net: `0.05701430211623638`
- max additive drawdown: `-0.3542816727765016`
- max single-trade positive gross share: `0.1086913314382138`
- break-even roundtrip cost: `21.202860423247284 bps`
- positive chronological 10-trade blocks: `4/5`

Block 5 was negative, with mean base-net `-0.03127989450795228`.

## Scientific decision

`TIER 2 — PROMOTED CANDIDATE — FRAGILE` remains unchanged.

Do not optimize around the failed readiness diagnostic. Do not open 2026 solely on the basis of this evidence. Any future Tier 1 attempt must be separately frozen, materially stronger, independent, and explicitly address single-trade sensitivity and late-2025 instability without selecting around them.
