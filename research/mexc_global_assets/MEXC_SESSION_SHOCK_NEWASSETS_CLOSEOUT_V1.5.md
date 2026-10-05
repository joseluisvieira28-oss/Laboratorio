# MEXC SESSION-WIDE SHOCK CLUSTER — NEW ASSETS V1.5 CLOSEOUT

Date: 2026-10-05
Run: `37281257285`
Artifact ID: `11332891338`
Artifact SHA256: `34f51b160841945af56f56465feb5385b015574bae415b94047afacacc2aebc4`

## Frozen design

Source:
- V1.4 run `37281000602`
- 34/34 new, previously unopened global-asset candidates passed MEXC + Binance + Bitget source transport.
- Source artifact SHA256: `74af7ac8d02c764555dbb24d8eb9329e02511ebdf4472545b9037a61b4265f51`

Frozen event rule:
- session 14:35–18:39 UTC
- 5-minute external return = mean(Binance, Bitget)
- abs external move >=50 bps
- same-sign external-minus-MEXC lag gap
- abs lag gap >=25 bps
- FOLLOW_EXTERNAL_CONSENSUS
- 5-minute forward horizon
- one equal-weight cluster per UTC timestamp
- global 5-minute cooldown; no overlapping cluster outcomes

Scientific PASS gate:
- >=20 clusters
- >=8 triggered days
- mean gross >0
- median gross >0
- cluster win rate >50%
- both chronological half means >0
- exact one-sided binomial p<0.05

Operational robust gate:
- scientific PASS
- mean and median after 16 bps round-trip >0

## Result

- raw triggered asset events: 450
- accepted timestamp clusters: 172
- triggered days: 17
- winning clusters: 93 / 172
- win rate: 54.0698%
- mean gross: +4.361730 bps
- median gross: +4.403897 bps
- chronological halves: +4.624754 / +4.098707 bps
- exact one-sided binomial p: 0.160787

Cost:
- 12 bps: mean -7.638270 bps; median -7.596103 bps
- 14 bps: mean -9.638270 bps; median -9.596103 bps
- 16 bps: mean -11.638270 bps; median -11.596103 bps
- 20 bps: mean -15.638270 bps; median -15.596103 bps

Scientific PASS: false
Robust API-fee survivor: false

## Verdict

`NO_EDGE_AT_FROZEN_V15_GATE`

This family was adequately populated; the failure is not an underpowered-event-count problem. The observed gross magnitude remains in the same ~4 bps regime as the earlier regular-session mechanism and is structurally below documented standard MEXC API round-trip costs.

No threshold reduction, horizon search, asset-specific rescue, retrospective retuning, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
