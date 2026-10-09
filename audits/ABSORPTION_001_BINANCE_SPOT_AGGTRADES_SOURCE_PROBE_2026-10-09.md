# ABSORPTION-001 — OFFICIAL BINANCE SPOT DAILY AGGTRADES SOURCE METADATA GATE
Date: 2026-10-09
State: ARCHIVE_METADATA_SOURCE_POSSIBLE / NO MARKET ROWS READ / OUTCOMES SEALED

Source-only GitHub run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37921852140
Artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37921852140/artifacts/11612740270
Script: absorption_failed_auction/binance_spot_archive_source_probe_v01.py

Seven immutable official-public Binance Vision **SPOT BTCUSDT aggTrades** daily ZIPs from 2026-10-02 through 2026-10-08 were found via HTTPS HEAD, each with corresponding official .CHECKSUM metadata (64-char SHA256, filename bound):
- 2026-10-02 — 16,302,876 compressed bytes
- 2026-10-03 — 4,643,822 bytes
- 2026-10-04 — 7,011,983 bytes
- 2026-10-05 — 12,728,276 bytes
- 2026-10-06 — 11,960,790 bytes
- 2026-10-07 — 35,833,390 bytes
- 2026-10-08 — 15,718,250 bytes
- TOTAL **104,199,387 bytes compressed**.

**This is a SOURCE-DOCUMENT/METADATA PASS ONLY**. ZIP bodies have NOT been downloaded in this probe, their contents have NOT been SHA-verified, and no trade rows, prices, outcomes, event classes or PnL have been opened. `GET .CHECKSUM` alone does NOT verify integrity of downloaded data.

## Scientific constraints for next technical transport gate
1. Download exact official files and verify each full-byte SHA256 against the frozen metadata; fail closed on corruption or unavailable file.
2. Parse spot Binance aggTrades with original buyer-maker semantics: isBuyerMaker=true means aggressive sell, false means aggressive buy.
3. Aggregate trades by true exchange trade timestamp into UTC 5-minute buckets; dedup unique aggTrade IDs, check day boundary and completeness.
4. Bind to SHA-verified authentic MM-V1 Vault 5-minute observations from 2026-10-02 09:25 UTC, **never** interpolate missing sensor bars or reuse old Sept/Oct1 baseline across the gap.
5. The current partial UTC day 2026-10-09 is NOT part of daily archives yet; its post-00:00 canonical aggTrades need prospective official public API coverage or must wait for a later signed daily archive.
6. The old classifier must still be subject to >=2,016 immediately preceding **consecutive valid forward bars**, >=99% transport coverage, and original frozen event definitions. Archive transport changes must not change science or open returns.
7. 2036 real contiguous **sensor** bars are proven source-only, but canonical spot aggTrades coverage remains **UNVERIFIED**. There are only 20 candidate sensor bars after baseline as of 2026-10-09 11:00 UTC, nowhere near >=100 qualified events per primary group.
8. Do not attempt orders, account reads, authenticated endpoints, public API abuse/rate-limit circumvention, or production deployment.

This source-only gate provides a credible bounded archive transport option in lieu of thousands of REST queries across historical weeks. It does not prove a tradable economic edge.
