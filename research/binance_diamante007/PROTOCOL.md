# BINANCE-DIAMANTE-007 — AUTHENTIC FREE HISTORICAL SPOT L2 SOURCE GATE
**Frozen 2026-11-23 before this study's first provider API request/download.**
**SOURCE/REPLAY ONLY** — zero signals, zero trading, zero PnL, zero payments, zero subscriptions.

## Why
- [BINANCE-006 PR #377] original 90d public Spot aggTrade source blocked on pre-frozen >250 MB size cap; no historical results from it.
- [BINANCE-006B PR #378] separate 1s bar flow-only historical hypothesis is NOT a direct L2 absorption test.
- [BINANCE-004 PR #375] and [BINANCE-005 PR #376] have immutable 30s sell-flow + 10bps bid depth resilience + 60s long counterfactual; must not be tuned based on source selection or opened protected future results.
- A credible historical L2 archive requires actual, permissioned **snapshots plus ordered per-price diff-depth**, proper Binance U/u, matching timestamps and ideally independent trades. Metadata alone is never proof.

## Primary candidate and frozen sample scope
Public third-party Hugging Face dataset: `MaximumLeverage/crypto-lob-stream` (author advertises MIT, Binance Spot BTCUSDT/ETHUSDT/SOLUSDT and reconstructed orderbook from 2026-06-03; these are claims to VERIFY, not accepted as facts). Fixed **BTCUSDT, August 2026** first sample, exactly three candidate objects:
- `depth/binance/BTCUSDT/2026-08.parquet`
- `snapshots/binance/BTCUSDT/2026-08.parquet`
- `trades/binance/BTCUSDT/2026-08.parquet`

Also inspect **metadata only** for ETHUSDT and SOLUSDT from the same month, no download unless a *separate* pre-registered scope is authorized. This avoids opening huge datasets before source qualification. No sample substitution from BTC to ETH, to later months or to a different provider after source errors.

### Public access, license and provenance
- One anonymous GET of `https://huggingface.co/api/datasets/MaximumLeverage/crypto-lob-stream`, one anonymous GET of recursive tree URL; no cookies, token, credential, VPN or blocked-source workaround. Require explicit public/gating=false/private=false and explicit MIT-compatible dataset license in model card or API; record **immutable revision SHA** and exact file paths, LFS object IDs if available, byte sizes and times.
- A declared license is not independent verification of right to redistribute exchange market data. No redistribution of raw archive as a public GitHub artifact. Keep only source manifests and small anonymized diagnostic metrics.
- Exact URL per file `https://huggingface.co/datasets/MaximumLeverage/crypto-lob-stream/resolve/{revision}/{path}`; reject HTTP redirects not on `huggingface.co`, `cdn-lfs*.huggingface.co`, `cas-bridge.xethub.hf.co`, `*.xethub.hf.co` as applicable. No authentication, no paywall.
- Download only if all 3 actual sizes known, **each <=80 MB**, combined <=160 MB, and transient memory/disk <=500MB; default only record metadata and **SOURCE_SIZE_BLOCKED** if exceeded. Limit 35-minute CI runtime. Abort on HTTP errors, no fallback or retries.
- Persist SHA256 original raw Parquet bytes, upstream file reported LFS SHA256 if present; do not claim independent cryptographic source verification if no external provider hash exists. Pin revision SHA, schema, timestamp first/last, level rows and sequence receipt.

## Actual L2 source gate
- Use read-only PyArrow to inspect schema of **all 3 original Parquet** objects. Required depth: `timestamp_ms,exchange,asset,side,price,quantity,first_update_id,last_update_id` (optional `exchange_ts`). Snapshot: `timestamp_ms,exchange,asset,side,price,quantity,last_update_id`. Trades: `timestamp_ms,exchange,asset,price,quantity,buyer_maker` (optional `trade_id`).
- Only `exchange=binance`, `asset=BTCUSDT`, bid/ask, positive finite price, nonnegative finite quantity; snapshot quantities positive, crossed/empty top invalid. Reject NaN, missing IDs, nonmonotone source ordering, conflicting duplicate levels within one snapshot.
- The nearest **first full snapshot with both sides and a unique lastUpdateId** is the only starting point. Discard diff events with `u<=snapshot.lastUpdateId`, accept first retained diff only if `U<=lastUpdateId+1<=u`. Subsequent event gap if `U>prev_u+1` -> **GAP_BLOCKED**; no retroactive splicing of later snapshots as uninterrupted source, log each reset as a new noncontinuous segment.
- Depth parquet contains **one row per changed level**, so group rows into complete event messages by contiguous `(timestamp_ms,U,u)`; never count a row as an independent WS message or skip a missing event; fail closed on noncontiguous repeats or ordering ambiguity. Apply the new quantity as absolute, delete if zero. Do not mistake quantity level removal for cancellation of an individual order.
- CRITICAL: snapshot stores **top 1000 levels per side**. A naive unlimited replay can retain ghost levels as best prices drift. Enforce **explicit bounded top-1000 visibility** as new levels enter, and record inability to certify full beyond-top-1000 book. Avoid false positives due to truncated books. A sanity cross check against any later snapshot is necessary before long continuous reconstruction claims.
- Source timestamps: receipt `timestamp_ms`, optional `exchange_ts`; ensure snapshot and diff temporal order reasonable, and trade stream covers a matching actual period; no post hoc event reordering to force success. Raw input may have capture gaps/restarts including known July 2026 interruption; treat such intervals censored rather than smoothing.
- This first test examines at most **200,000 L2 price-level rows** after the first bridge for source feasibility, with maximum 30min of source span; **not a full month or 90-day L2 test**. Report exact checked window and fraction vs entire original file rows, never imply all history validated.

## Results and economic gate
- Primary permitted outcomes: `PROVENANCE_METADATA_PASS`, `REAL_L2_WINDOW_REPLAY_PASS_ONLY`, `SOURCE_BLOCKED`, `GAP_BLOCKED`, `TIMESTAMP_BLOCKED`, `SIZE_BLOCKED`, `LICENSE_BLOCKED`.
- No SIGNALS, no PnL, no win rate and no strategy tuning on this source-qualification run. Even a tiny verified L2 interval cannot validate BINANCE004's 30s/60s sell-flow hypothesis; that demands a second, independently pre-frozen **new** historical L2 test sample (avoid selecting the same data as both exploration and proof), realistic slippage, spread/fees, independent holdout, and unmodified future 005.
- Keep PR DRAFT and never merge. No paid data, credit card, paid runners, public original raw market-data artifact, exchange API keys, live orders, simulation orders placed on exchange, deposits, futures, private APIs, production, Render or Telegram changes.

Sources:
- https://huggingface.co/datasets/MaximumLeverage/crypto-lob-stream
- https://docs.tardis.dev/historical-data-details/binance
- https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams
