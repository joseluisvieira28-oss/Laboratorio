# Economic Forward V1.0 — source verdict, 2026-11-04

Original source-only run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41872000026

- Frozen preregistration before market data: commit 88e7632c77c2d0fccc856d59d621caaf5f590658.
- Workflow run/code SHA 8d27b413e8f17053b50c3ebe3a06cb05d5c952be.
- Original raw artifact 13344184977. Downloaded ZIP SHA256 db72f8e6f44601a4f32021958b8e69e65ea840358feecf6ede136d10249c00f1. Uncompressed raw NDJSON SHA256 9ca6b75b1f4062e713ecac8a6f43e82f20c8c96e621ccfac2f8308a607b3ab38.
- 240sec public transport, 12195 raw frames, no disconnects. Bybit: 9366 contiguous order-book deltas and 5903 executed trade children, 0 liquidation children observed in this bounded window (not a certified market-wide zero).
- MEXC: 94 real BTC_USDT Futures ticker best-bid/ask packets: 30 within frozen 1500ms age, 64 stale; observed packet lag roughly 325ms to 4326ms, median about 2205ms.
- Original collector reported 18 eligible MEXC quotes because its post-stale three-message quarantine was sticky. Independent replay of original source with strict re-quarantine yields only 1 eligible quote. The bug has been corrected for future source code; original run is NOT changed.
- Pilot original final status MEXC_EXECUTABLE_QUOTE_SOURCE_BLOCKED. Zero economic outcomes opened, zero PnL; no trading.
- New DISTINCT source-only technical probe: MEXC five-level full-depth snapshots, preregistered in DEPTH_SOURCE_ALTERNATIVE_FREEZE_V1_1.md before separate observations. Preserve original economic numerical thresholds and do not retrofit economic results.
