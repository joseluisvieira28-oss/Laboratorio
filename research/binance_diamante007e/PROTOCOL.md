# BINANCE-DIAMANTE-007E — AUDITED SMALL SOURCE BUDGET EXTENSION (NO OUTCOMES)

**NEW independent SOURCE-ONLY experiment, pre-registered 2026-11-23 before original Goooddy SOL August Parquet bytes are ever downloaded/read by us.** All prior BINANCE007/007B/007C/007D outcomes and budgets unchanged.

## Background and source preflight
BINANCE007D [PR #383](https://github.com/joseluisvieira28-oss/Laboratorio/pull/383) had 24/24 offline guards PASS but source returned `FILE_TOO_LARGE_depth_86734108` from immutable public Hugging Face metadata, just exceeding its 80,000,000-byte per-file cap. This was **pure file metadata**, not trading prices, PnL, or insight from the order book. The dataset author's claimed MIT license and no-auth public catalog are known. No raw market bytes downloaded by 007D. The provider advertises a June-Aug flush/overwrite capture bug, so even a successful short gap-free source segment cannot validate August's full chronology.

## Distinct scope/operational budget
The **same** asset and period, Goooddy/crypto-lob-stream, Binance Spot SOLUSDT, August 2026, exact 3 pinned Parquet objects `depth/binance/SOLUSDT/2026-08.parquet`, `snapshots/binance/SOLUSDT/2026-08.parquet`, `trades/binance/SOLUSDT/2026-08.parquet`, immutable SHA from provider.
- **Budget only change**: single file cap increases from 80,000,000 to **90,000,000 bytes** (the published original depth file is 86,734,108 bytes). Overall max stays **160,000,000 bytes**, standard GitHub public hosted runner, no payments, no subscriptions, no private API, no VPN/bypass. If the 3-file total >160MB, stop. No more budget revision or same-day retries after this.
- ALL original `research/binance_diamante007/source_probe.py` and `book_replay.py` source, event, temporal, fee/no-economic guards unchanged. Only a wrapper declares the separate metadata-based source budget, at a new PR on a stacked research branch. Original source ZIP/Parquet bytes never uploaded to the public repo.
- Force original source hash check against Hugging Face LFS SHA256 if present; snapshot >=100 levels both sides, initial bridged Binance U/u coverage, <=200k price-level changes or <=30min of first source span, no crossed/empty book, top1000 ghost-level prune; >=500 real applied depth events AND >=1 overlapping trade, otherwise BLOCKED.
- SOURCE only: no historical economic outcomes, no lookahead selection, no hypothetical signal returns, no trading, no money, no accounts/keys, no futures, no merges, no 004/005 modifications, no other data provider substitution after error.

## Verdict
`REAL_L2_BOUNDED_WINDOW_REPLAY_PASS_ONLY` only if real public files, actual SHA and sequence replay, clocks and trade overlap pass. The known overwriting bug forbids promoting a clean SHORT window into whole-month/90-day source integrity. Real execution/alphas always unproven. No further same-day re-requests or alternate fee/strategy tuning.

Sources:
- https://huggingface.co/datasets/Goooddy/crypto-lob-stream
- https://github.com/Goodie-Goody/crypto_lob_stream_pypi/releases/tag/v0.9.2
