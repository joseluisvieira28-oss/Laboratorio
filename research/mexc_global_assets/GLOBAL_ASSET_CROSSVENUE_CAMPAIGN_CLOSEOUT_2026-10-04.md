# MEXC GLOBAL ASSETS — CROSS-VENUE CAMPAIGN CLOSEOUT — 2026-10-04

Status: RESEARCH-ONLY / NO LIVE TRADING AUTHORIZATION

## 1. SP500 — replicated MEXC contract/index basis signal

Frozen cell:
- MEXC `SPX500_USDT`
- FADE contract-vs-index basis
- absolute threshold: 5 bps
- horizon: 15 minutes

August retrospective OOS:
- N=809
- win rate=53.1520%
- mean gross=+0.4601053 bps
- p=0.0393495
- both chronological halves positive

Untouched September holdout:
- N=654
- win rate=54.4343%
- mean gross=+0.5177568 bps
- p=0.0128735
- both chronological halves positive

Classification:
`REPLICATED_SIGNAL_SURVIVOR__EXECUTION_FEASIBILITY_UNPROVEN`

Published standard API execution fees materially exceed this gross effect, so standard API automation is fee-blocked absent a lower verified route.

## 2. SP500 — Hyperliquid real-time lead/lag

Source binding:
`MEXC SPX500_USDT <- Hyperliquid xyz:SP500`

Frozen V0.4 discovery:
- 4,860/4,860 exact 1m overlaps
- 36 cells
- pre-Holm eligible=0
- Holm-selected=0
- widest gate produced only N=4

Verdict:
`NO_EDGE_AT_FROZEN_V04_GATE`

## 3. NAS100 — Hyperliquid source binding

MEXC declares `indexOrigin=["HYPERLIQUID"]`.

Public Hyperliquid candidates `km:USTECH` and `mkts:USTECH` were on a materially different price scale from MEXC NAS100 and no defensible public transformation was identified.

Verdict:
`SOURCE_BLOCKED_HYPERLIQUID_NAS100_IDENTITY`

Outcomes opened: 0.

## 4. NVIDIA — Bitget lead/lag

Source gate:
`NVDA_BITGET_MEXC_SOURCE_PASS`

Probe:
- MEXC=234.84
- Bitget=234.85
- dispersion~0.4258 bps
- public 1m clocks pass

Frozen V0.7 discovery:
- coverage=99.8971%
- 36 cells
- pre-Holm eligible=0
- Holm-selected=0

A 10bps shock / 5bps gap / 15m cell showed +26.2bps gross but N=5 only. It is NOT a candidate and must not be cherry-picked after outcomes.

Verdict:
`NO_NVDA_CROSSVENUE_DISCOVERY_CANDIDATE_AT_FROZEN_V07_GATE`

## 5. GOLD — Bitget lead/lag

Source gate:
`GOLD_BITGET_MEXC_SOURCE_PASS`

Probe:
- MEXC=4145.50
- Bitget=4144.54
- dispersion~2.3163 bps
- public 1m clocks pass

Frozen V0.9 discovery:
- coverage=99.8971%
- 36 cells
- pre-Holm eligible=0
- Holm-selected=0

Widest gate 3bps shock / 2bps gap:
- 1m N=17, mean +1.1948bps, win 47.06%
- 2m N=15, mean +1.4277bps, win 46.67%
- 5m N=14, mean +1.1678bps, win 50%
- 15m N=13, mean -8.1015bps, win 7.69%

Verdict:
`NO_EDGE_AT_FROZEN_V09_GATE`

## Overall campaign verdict

The campaign produced one genuinely replicated scientific signal:

`SP500 MEXC CONTRACT/INDEX BASIS — 5BPS — 15M — FADE`

It did NOT produce a defensible short-horizon external-venue lead/lag candidate in SP500, NVIDIA or GOLD, and NAS100 remains source-blocked.

The legitimate next stage is execution-quality measurement and future-forward shadow observation of the replicated SP500 basis signal, without retuning it.

No merge to main, live trading, account reads, private endpoints, wallets, orders or exchange mutation were performed.
