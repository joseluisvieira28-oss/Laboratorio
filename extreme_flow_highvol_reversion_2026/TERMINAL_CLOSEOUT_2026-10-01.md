# EXTREME-FLOW-HIGHVOL-REVERSION-2026-001 — TERMINAL HOLDOUT CLOSEOUT

Date: 2026-10-01
Classification: **HOLDOUT_FAILED**
Branch: extreme-flow-highvol-reversion-2026-v0.1
Workflow run: 36876438704
Artifact: 11168793023
Artifact SHA256: 0f07cbbfcaf171186fc00139263029c48d74297d29627e29dcf853a70f25ac15

Discovery-derived rule frozen before 2026 access:
- extreme flow q95
- base volume >= 2.0 x rolling q75
- 60m cooldown
- fade aggressor direction
- primary horizon 240m

2026-01-01 through 2026-09-30 holdout:
- source coverage: 100%
- valid 5m bars: 78,624 / 78,624
- accepted events: 331
- distinct UTC dates: 185
- F240 coverage: 99.6979%
- gross mean F240: +1.6696 bps
- gross median F240: +2.9647 bps
- gross PF: 1.0527
- hit rate: 51.5152%
- Wilson lower95: 46.1367%
- bootstrap95 mean F240: [-7.8502, 11.6278] bps
- positive-median quarters: 2/3
- Q1 median +13.8074 bps
- Q2 median +2.4973 bps
- Q3 median -3.4750 bps

Gross confirmatory gate failed.

Current MEXC API fee-only models:
- 12 bps RT maker-maker: mean net -10.3304 bps, PF 0.7273, bootstrap95 mean net [-19.8502, -0.3722]
- 16 bps RT taker-taker: mean net -14.3304 bps, PF 0.6433
- stress 14/18 bps also fail

This 2025 discovery enhancement did not replicate in the 2026 holdout and is not execution viable under the frozen current MEXC API cost model.
No rescue or retuning under this identity.
Trading authority: NONE.
