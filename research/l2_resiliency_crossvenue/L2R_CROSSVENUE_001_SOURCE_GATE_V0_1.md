# L2R-CROSSVENUE-001 — SOURCE GATE V0.1

Date: 2026-09-30

Status: **SOURCE_TIMING_READY / PARENT_ANCHOR_BYTES_BLOCKED**

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


## 2026-10-01 source-timing advance

A source-only Binance cadence preflight was completed without parsing price values or computing returns.

Evidence:
- GitHub Actions run `36816039423` = PASS;
- artifact ID `11141960210`;
- artifact digest `sha256:22de1277f5b87da2c1ff0bb8c6a89b75170d6830bee9eca469880956cdc3a336`;
- 20/20 frozen 2024 daily aggTrades ZIPs passed official SHA256 checksums;
- 26,709,512 inter-aggTrade gaps measured;
- global p99 = 946 ms;
- global p99.9 = 1,947 ms.

External timing is now prospectively frozen:
- first Binance aggTrade at-or-after target;
- no interpolation;
- no backward fill;
- maximum lateness = 2,000 ms;
- derivation = ceil(global timestamp-only p99.9 / 100 ms) × 100 ms.

The exact parent anchor ZIP was also located in the user's historical Library:
`/Crypto/L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.zip`
(size 200,205,120 bytes).

However, the current runtime cannot export its raw bytes. This is a transport/materialization blocker only. No 2024 cross-venue outcome may be opened until the inner CSV verifies exactly to:
`be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`.
