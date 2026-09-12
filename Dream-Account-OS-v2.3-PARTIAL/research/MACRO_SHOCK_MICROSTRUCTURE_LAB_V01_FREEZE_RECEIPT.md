# Macro Shock Microstructure Lab V0.1 — Freeze Receipt

Authoritative contract:
`Dream-Account-OS-v2.3-PARTIAL/research/MACRO_SHOCK_MICROSTRUCTURE_LAB_V01_PROSPECTIVE_RESEARCH_CONTRACT.json`

Freeze commit:
`8cd68107de392837216012cba3b4f0edb369313b`

Implementation-gate commit:
`746eac08d7b3348fb2382a526e3ce9ea5c658599`

Scientific status:
`FROZEN_PRE_HOLDOUT`

Primary hypothesis:
`MSM_H01_FLOW_PERSISTENCE_CONTINUATION`

Frozen market scope:
- Binance Spot
- BTCUSDT
- ETHUSDT
- US CPI
- US NFP
- US FOMC

Frozen windows:
- flow window 1: 0–5 min post-release
- flow window 2: 5–15 min post-release
- outcome window: 15–30 min post-release

Primary statistic:
`continuation_rate_difference`

Classification states:
- SURVIVES
- NO_EDGE
- INSUFFICIENT_SAMPLE
- TECHNICAL_OR_DATA_FAILURE

Critical governance:
- 2026 holdout remains locked
- MEXC Sep–Dec 2025 remains locked
- no live trading
- no exchange mutation
- no merge to main
- no Render deployment

Next permitted stage:
`PRE_HOLDOUT_IMPLEMENTATION_AND_SYNTHETIC_TESTS_ONLY`

Stop condition:
`STOP_BEFORE_2026_OUTCOMES_UNTIL_SEPARATE_EXPLICIT_HOLDOUT_UNLOCK`
