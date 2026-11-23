# BINANCE-DIAMANTE-007B — SECOND SOURCE QUALIFICATION, NOT A STRATEGY CHANGE

**Pre-registered 2026-11-23 before 007B's first provider API request.**
Fresh independent source qualification, separate from failed 007 PR #380.

## Why new provider, and why September
The original 007 dataset `MaximumLeverage/crypto-lob-stream` responded to public metadata, but the exact frozen BTCUSDT August 2026 depth/snapshot/trades paths were MISSING on API file tree (first 007 run #45171836922 SOURCE_BLOCKED, no archive downloads or economic outcome). Preserve original failure and DO NOT alter first trial.

New source is `Goooddy/crypto-lob-stream`, separately hosted/public, using the explicit *post-August 2026* period. Its README warns that the original June–August 2026 collector silently overwrote flushes within each clock hour; September is intentionally chosen to avoid a **known, documented data-integrity bug**, not on any observed strategy returns. This source may still fail. No assumption of full continuity or source quality before independent verification.

## Frozen exact source
- BTCUSDT Binance Spot, **2026-09**. Exactly three pinned monthly public Parquet files: `depth/binance/BTCUSDT/2026-09.parquet`, `snapshots/binance/BTCUSDT/2026-09.parquet`, `trades/binance/BTCUSDT/2026-09.parquet`.
- ETHUSDT and SOLUSDT metadata presence/size check only.
- Dataset `Goooddy/crypto-lob-stream`. Reject private/gated dataset, missing explicit MIT-compatible license, missing 40-character immutable git SHA, any pinned file missing or larger than 80 MB, or combined original files >160 MB. Anonymous public HTTPS GETs only. No credentials, subscriptions, payments, VPN, API key or workaround.
- Reuse **exact** pre-reviewed `research/binance_diamante007/source_probe.py` and `book_replay.py` on the source branch as immutable library modules. No parameter changes except dataset ID, exact asset/month paths and artifact prefix, all declared in the wrapper. No user account access, exchange requests, actual paper orders or real orders.
- Preserve original SHA256 of raw third-party file downloads and compare upstream Git LFS SHA256 if published; raw files remain in private ephemeral runner tempdir, NEVER uploaded to GitHub public artifacts.
- Strict same Binance `U/u` book bridge, crossed book, timestamp, top-1000 ghost-level cap, max 200,000 changed-price rows or 30 minutes of source; >=500 applied independent WS events plus at least 1 overlapping real trade row required. Never equate diff rows to separate events.
- Protocol cannot yield 90-day L2 completeness, 004-style economic alpha or executable profits. This SOURCE gate is a prerequisite for a future **new preregistered independent** economic backtest, which must be split chronologically without using sample 007B to pick winning thresholds.

## Final governance
`REAL_L2_BOUNDED_WINDOW_REPLAY_PASS_ONLY` if all source, license, provenance, snapshots, U/u, no gaps, chronology and trade alignment pass. Otherwise `SOURCE_BLOCKED`. A green CI by itself is NOT edge. Keep DRAFT, stacked on 007 research branch. **Never merge, trade, deploy, spend money, alter main or alter frozen BINANCE-004/005/006/006B**.

Evidence:
- https://huggingface.co/datasets/Goooddy/crypto-lob-stream
- https://huggingface.co/datasets/MaximumLeverage/crypto-lob-stream
- https://github.com/Goodie-Goody/crypto_lob_stream_pypi/releases/tag/v0.9.2
