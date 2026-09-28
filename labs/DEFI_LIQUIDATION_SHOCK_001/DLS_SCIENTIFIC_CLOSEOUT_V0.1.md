# DEFI-LIQUIDATION-SHOCK-001 — SCIENTIFIC CLOSEOUT V0.1

Date: 2026-09-28
Status: TERMINAL FIRST EXPERIMENT
Canonical classification: SURVIVES_OOS

## Canonical chain

- GLOBAL_FIELD_COVERAGE_FINAL_PASS — run 36464851648
- SOURCE_SAMPLE_GATE_PASS — run 36465385517
- MARKET_DATA_SOURCE_PASS — run 36483390920
- FINAL_PRE_DISCOVERY_AUTHORITY_PASS — run 36483501137
- SURVIVES_DISCOVERY — run 36485865469, artifact 10999736255
- SURVIVES_OOS — run 36486620726, artifact 10998958189

## Discovery

- paired N: 5,672 / 5,672 directly mapped clusters
- pair coverage: 100%
- primary 5m mean paired absolute-move difference: 0.0018118444614170762
- primary 5m relative uplift: 76.55965972071541%
- primary 5m day-block bootstrap 95% CI: [0.0010973568077898503, 0.002648111131283935]
- all frozen Discovery gates: PASS

## OOS 2024

- mapped clusters: 9,931
- paired clusters: 9,929
- pair coverage: 99.97986104118417%
- two split-boundary clusters excluded prospectively
- hard market-data errors: 0
- primary 5m mean event absolute move: 0.0032568710857610117
- primary 5m mean control absolute move: 0.0018006646541898945
- primary 5m mean paired difference: 0.0014562064315711174
- primary 5m relative uplift: 80.8704956907289%
- primary 5m day-block bootstrap 95% CI: [0.0010233675821834868, 0.0019805261175959497]
- one-sided bootstrap p: 0.0001999600079984003
- every frozen OOS gate: PASS

Protocol-family 5m paired means:
- Kamino: +0.0025814313333364577 (N=2,123)
- marginfi: +0.0011462500035786304 (N=6,019)
- Save11: +0.0011634113972336594 (N=1,787)

Secondary OOS paired means are positive at 1m, 30m and 240m.

## Interpretation boundary

SURVIVES_OOS means the frozen causal-event experiment survived both Discovery and the independent 2024 OOS under its prospectively frozen statistical gates.

It is not live-trading authority and is not yet evidence of a directly executable trading strategy. The V0.1 primary claim concerns larger absolute post-liquidation market movement, not a universal signed direction.

## Protected holdout

2025 and 2026 market outcomes remain CLOSED.
No protected-holdout authority is created by this closeout.
No live trading, orders, wallets, exchange mutation, post-outcome tuning, or merge to main is authorized.

## Canonical evidence hashes

Discovery result:
d75081066e885e835ecf915673d10af64a53fe4f298e5b2a8d4a287f9c12ea2d

OOS result:
ac5852c1a1cbc2f8f29d6bbfcc7527bf00c3420e0e5e54b729fcaa310ae74da3

OOS acquisition:
74b7a898232569367de635d257ec34709c6cf86ca8bbc4a4aeda0ad9f6014b97

OOS paired outcomes:
fc0154fcd1a65f60342bcb8eb786289f621c53394ff10a753f6944382c135c24

OOS archive manifest:
fedc04778b0aafd7c83b67c479368487df40fd4fa93e46bcc497504dad9668c3
