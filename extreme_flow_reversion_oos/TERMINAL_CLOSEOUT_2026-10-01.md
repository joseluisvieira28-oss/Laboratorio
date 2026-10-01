# EXTREME-FLOW-REVERSION-OOS-001 — TERMINAL OOS CLOSEOUT

Date: 2026-10-01
Classification: **OOS_REVERSION_SURVIVES**
Branch: extreme-flow-reversion-oos-v0.1
Workflow run: 36875363721
Artifact: 11168806456
Artifact SHA256: 9b4e6c045663dcb60a0defb3f51c3b11901bf23dac1f70dfcc3d8f32e158c19c

Untouched 2025 OOS:
- accepted events: 948
- distinct UTC dates: 326
- source coverage: 100%
- R60 coverage: 100%
- median signed R60: -2.4024 bps => fade median +2.4024 bps
- bootstrap95 signed median: [-4.7749, -0.3165] bps
- reversal rate: 53.5865%
- Wilson lower95: 50.4038%
- 4/4 quarter medians negative in signed aggressor direction

This is a real replicated statistical mean-reversion mechanism under the frozen test, but the effect is small.
Post-OOS economic diagnostic on the fixed 948-event ledger:
- gross fade mean: +2.4075 bps
- gross fade median: +2.4024 bps
- gross PF: 1.1786
- approximate round-trip break-even expectancy: 2.4075 bps
- at 2 bps RT: mean +0.4075 bps, PF 1.0282
- at 3 bps RT: mean -0.5925 bps, PF 0.9603

Therefore this result is mechanism evidence, not a current execution edge.
Trading authority: NONE.
