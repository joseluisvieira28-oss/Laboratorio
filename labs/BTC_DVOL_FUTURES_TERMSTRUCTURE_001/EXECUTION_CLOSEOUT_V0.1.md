# BTC-DVOL-FUTURES-TERMSTRUCTURE-001 — DIRECTIONAL EXECUTION MVE CLOSEOUT V0.1

Date: 2026-09-17
MVE: DVOL-TS-DIRECTIONAL-EXEC-001
Canonical run: 35279459899
Head SHA: b1102cf36212b796b0ebe214349e50fa312f4e3c
Artifact ID: 10522345673
Artifact ZIP SHA256: 0f250b09ca3100aef21b080d4edb6d2c36be60749afa45b94797f2d99ebb0b66
Source receipt SHA256: 5b41f2a968847896b9ee82605715cc391cfd57a38cefa83fa9975bb575540828

## FINAL CLASSIFICATION

EXECUTION_DATA_LIQUIDITY_INSUFFICIENT

## SAMPLE

- executable episodes: 27
- contracts with episodes: 12
- expiration quarters: 6
- minimum frozen episodes required: 120
- no-entry direction-matched fill exclusions: 189
- no-exit direction-matched fill exclusions: 55
- zero-basis exclusions: 3

The frozen sample gate failed and may not be repaired by widening the 30-minute fill window under this MVE ID.

## OBSERVED ECONOMIC DIAGNOSTICS (NON-PROMOTABLE)

Even within the insufficient sample, every frozen economic gate failed:
- mean per-contract base net: -0.0972161458 USDC
- median per-contract base net: -0.0849875 USDC
- base PF: 0.195899
- contract-cluster bootstrap 95% CI: [-0.1604969, -0.0349245] USDC
- positive contract share: 25%
- nonnegative quarters: 2/6
- stress mean per-contract net: -0.1185861545 USDC
- stress PF: 0.124825
- max positive-contract contribution share: 57.34%

These figures are not a valid promoted performance estimate because the sample gate failed, but they provide no positive evidence for this directional implementation.

## INTERPRETATION

The parent Discovery remains valid: futures-minus-index basis converges statistically. This MVE tested a different question and found that taking naked directional DVOL-futures exposure after the signal is both difficult to fill under strict public-trade semantics and economically adverse in the recovered subset. Common DVOL-index movement can dominate the basis-convergence component.

## NO RESCUE

Do not widen fill windows, reduce costs, use the signal print as the fill, lower N=120, delete losing contracts, change direction, or select a basis threshold under DVOL-TS-DIRECTIONAL-EXEC-001.

A future study must be materially different and prospectively justified before outcomes. One legitimate separate question is whether adjacent DVOL futures provide enough simultaneous liquidity to hedge common DVOL-index movement through a near-vs-far calendar spread.

2025/2026 access: false
Live trading: false
Exchange mutation: false
Merge to main: false
