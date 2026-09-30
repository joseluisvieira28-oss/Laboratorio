# L2R-CROSSVENUE-001 — SOURCE GATE V0.1

Date: 2026-09-30

Status: **SOURCE_READY / PARENT_ANCHOR_MATERIALIZATION_BLOCKED**

## Source facts

A prior source-only probe verified 20/20 Binance BTCUSDT spot aggTrades daily objects in 2024 across four quarters. No returns were computed.

Later canonical L2 receipts establish that the Hyperliquid 2024 BTC source was successfully preserved and processed:
- 8,707 present hourly objects;
- 6,832,137,900 compressed bytes verified;
- schema normalization PASS;
- sweep-event preflight PASS;
- horizon-timing preflight PASS;
- parent 2024 Discovery completed.

The 20 dates used by the old cross-venue source probe are present in the preserved 2024 source inventory.

## Remaining blocker

The event-level parent artifact was not found in the currently connected Library, Drive, repository, or surviving Actions artifacts.

Expected artifact:
`L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.csv`

Recorded SHA256:
`be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`

Aggregate receipts are not sufficient to reconstruct individual event timestamps.

The next valid step is either:
1. recover that exact anchor artifact; or
2. restore the preserved 2024 raw L2 bodies and deterministically regenerate it under the parent rules.

## Firewalls

- Binance returns opened: false
- cross-venue responses computed: false
- 2025 cross-venue outcomes opened: false
- 2026 access: false
- scientific rules changed: false
- main merge: false
