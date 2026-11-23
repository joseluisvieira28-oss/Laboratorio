# BINANCE-DIAMANTE-007D — A REAL SMALLER PUBLIC SPOT L2 WINDOW, SOURCE ONLY

**PRE-SOURCE frozen 2026-11-23**; independent and separate from source-blocked #380 and #381 and catalog-only #382.

## Scientific explanation for choosing smaller source
The catalog-only historical metadata audit in #382 established that `Goooddy/crypto-lob-stream` has an August 2026 Spot `BTCUSDT` L2 file (~311.2 MB) but its September files do not exist. The 007/007B 80 MB single-file cap and 160 MB total limit must NOT be silently changed. This new dataset-source feasibility study selects **SOLUSDT / 2026-08**, likely smaller than BTC and therefore a fresh appropriately pre-registered candidate. We have NOT checked SOL August file sizes or read price/order-book rows before this freeze. Treat this candidate as SOURCE_BLOCKED if absent or oversized.

CRITICAL: Author Goooddy reports known 2026 June–August flush overwrite bug. This was written in public dataset README before this trial. Therefore even if one source L2 segment replays cleanly, **this dataset cannot be considered continuous or statistically representative for the full month without an independent detailed gap audit**. Do not use clean short segments to overwrite this known source-risk warning or to declare economic GO.

## Frozen source, size and replay scope
- Exactly `Goooddy/crypto-lob-stream` at the immutable 40-character revision returned by public Hugging Face API; pinned paths `depth/binance/SOLUSDT/2026-08.parquet`, `snapshots/binance/SOLUSDT/2026-08.parquet`, `trades/binance/SOLUSDT/2026-08.parquet`; BTC/ETH presence/size metadata only.
- Exact same code, guards, and price-level event reconstruction from original BINANCE007: strict 3 file LFS SHA256 original input, must be public, no gated login, MIT license declared, <80MB each and <160MB total, <=200k depth price-level rows or 30min original source interval, >=500 valid bridged depth events, 1000-level snapshot and ghost-level prune, real trades share audited window.
- Never re-run original blocked 007/007B attempt; branch stacked on them without modifying their files or historical protocol. Single one-off public standard GitHub runner <=25min. No keys/account access, paid data/subscription, charge, exchange trading API, paper or live orders, capital, margin, Futures, production, Render/Telegram, or merge to main.
- No numeric trade forecasts, profitability labels, 004 threshold tune or opening 005 future outcomes. Original HF archives stored only ephemerally; public GitHub artifact contains source hashes, file sizes and diagnostics, not original third-party market-data bytes.

## Gate
`REAL_L2_BOUNDED_WINDOW_REPLAY_PASS_ONLY` requires all actual original checks and no gap, WITH explicit warning of publicly documented June-Aug overwriting risk; otherwise `SOURCE_BLOCKED`, with exact first reason. A clean bounded window does NOT establish full-month L2 integrity, 90-day sample or executable alpha. Further independent prospective / historical data source science must be separately registered before economic outcomes or trading.

References:
- https://huggingface.co/datasets/Goooddy/crypto-lob-stream
- https://huggingface.co/datasets/MaximumLeverage/crypto-lob-stream
- https://github.com/Goodie-Goody/crypto_lob_stream_pypi/releases/tag/v0.9.2
