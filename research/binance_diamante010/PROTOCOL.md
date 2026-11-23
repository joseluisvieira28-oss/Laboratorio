# 💎 BINANCE-DIAMANTE-010 — 30-MINUTE LONGER FROZEN 004-STYLE PROSPECTIVE L2 SOURCE PILOT
**PRE-REGISTERED 2026-11-23 BEFORE the first BINANCE010 market source read.**
**No real/exchange test orders; no private accounts, subscriptions, payments, premium runners, production, merge, or modification to BINANCE004/005.**

## Scientific identity and separation
Study ID: `BINANCE010-FROZEN-004-RULE-30MIN-INDEPENDENT-SOURCE-PILOT-V01`.
Motivation: BINANCE005 scheduled daily study collects 8 minutes/day; cannot easily satisfy >=200 matured primary observations across >=20 UTC days. Previously tested 2026-08 historical third-party L2 downloads were byte-verified but lacked required snapshot `side` and `last_update_id` fields and upstream producer documented a June–August capture overwrite defect. A pure public Binance Spot **prospective** WS + REST snapshot avoids depending on this unreliable historical L2 source.

**Important:** this is a NEW, separately preregistered extended-length experiment; it is NOT *exactly the same trial* as original BINANCE004/005 because the capture horizon and allowed decision interval are increased. The **per-window economic hypothesis is the same** but longer periods can experience more spread/depth drift and correlated events. Never pool as independent if same UTC day or overlapping source times. Original BINANCE004/005 branches and all closed holdouts are untouched.

## Frozen source / code before first data
- Reuse the original, completely unedited modules from BINANCE004/003 and prevent drift by immutable Git blob SHA gate:
  - `research/binance_diamante004/PROTOCOL.md` = `b1b8d2aa2b9dd4853e04671de0d96336ae895d1b`
  - `research/binance_diamante004/capture_forward.py` = `ef8a987e026656cd3a60d402761c21078dee3ca7`
  - `research/binance_diamante004/study.py` = `58cf6af9c0ba26da2ac9efa700c103b93c7580b5`
  - `research/binance_diamante004/verify_offline.py` = `33ca9731cbbb2d4f22db8d5309d4616bfe3ca616`
  - `research/binance_diamante003/book_core.py` = `9b2a92455d36dc251ec99a2754c07a7f91a9af91`
  - `research/binance_diamante003/capture.py` = `490ad52bef283dedb4036e8793f6892788803a0e`
- No editable strategy/fee/symbol thresholds in 010; any code drift fail closed BEFORE source capture.
- Exactly one anonymous original live Binance Spot combined WS `wss://data-stream.binance.vision`, BTCUSDT, ETHUSDT, SOLUSDT, `@depth@100ms` and `@aggTrade`. Exactly one public `data-api.binance.vision` REST snapshot (`limit=1000`) per symbol after first diff; no reconnect, retries, auth, order, future, geographic workaround or account access. Original original-byte SHA256 journal with immutable hash chain, receipt arrival wall and monotonic clocks, BBO consistency, price-depth U/u sequence bridging.

## One pilot — fixed 1800-second post-bridge capture (not a 30-day claim)
- Single 1800sec **30-minute post-snapshot bridge** session; fail if total trial crosses UTC midnight. The script doesn't change original per-window classification; each 30s nonoverlapping receipt-time window is frozen exactly as 004.
- The ONLY scientific timing changes via a separately documented wrapper:
  1. `capture_forward.SECONDS_POST_SYNC` **480 -> 1800 seconds**.
  2. `study.CAPTURE_NS` **480e9 -> 1800e9**.
  3. `study.LATEST_DECISION_NS` **360e9 -> 1680e9**; reserve final 120s to let 60sec exits mature even if source is late; eligibility starts at 30sec and stops at 1680sec.
  4. Original 004 `ProspectiveStudy._advance` contains a **hard-coded cap `self.idx < 16`**; wrapper replaces ONLY this cap with `self.idx < 60`, retaining exact same `_window_close` method, no altering thresholds or statistical cohort logic. Fully test 60 windows × 3 assets, cutoff, no 61st window.
  5. `capture_forward.MAX_FRAMES` **40,000 -> 250,000** and `MAX_JOURNAL_BYTES` **50,000,000 -> 220,000,000** for longer collection. First oversize/source-gap stops study with failure, NO restart. Original journal 220MB cap is upper bound, not forecast storage spend.
- Every other 004 rule identical: sell share >=65% of Binance `m=true` aggressive aggregates and >=5000 USDT quote/30s, visible bid-depth within 10bps persistence >=80%, midpoint floor >=-3bps, fresh start/end book <=2s, no clock-invalid frames, 120s cooldown per signal kind/symbol, quote **LONG** next fresh diff within 3s; exit first subsequent diff >=60s from entry <=3s latency.
- Baseline unconditional long every fourth valid interval per symbol; flow-only control prespecified. They can overlap; never sum sample counts as independent.
- Hypothetical quote walks 100 and 1000 USDT. Base = 10bps taker +2bps adverse slip each side; Stress = 10bps taker +5bps adverse slip each side; quoted notional is NOT executable fills and account-specific Swiss eligibility and fees are UNKNOWN.
- Event returns, quote coverage, censored late/invalid rows, day UTC, original source/decision ledger SHA256 and re-reading exact 003/004 source+decision modules are required, no outcome smoothing.

## Decision gates
- One 30-min run is by definition **SOURCE/FEASIBILITY** only. It cannot pass >=20 distinct UTC days. Even if positive on this one day, **NO ECONOMIC GO**.
- Potential later expansion to 20+ new UTC days requires independent explicit daily single-attempt trigger, no overlapping capture windows with 005 counted as independent, 200 matured primary events across >=20 distinct accepted UTC days, mean stressed net>0, fixed-seed 10,000 whole-day-cluster 95% bootstrap lower>0, outperform no-trade, flow-only and unconditional baseline, no single UTC day >20% of positive profit, further new out-of-sample replication.
- If sparse primary signals, high missing source, any 003/004 book gap, clock anomalies, delayed quotes, or raw journal cap, mark `SOURCE_BLOCKED` or `INCONCLUSIVE`; don't rescue by relaxing thresholds or selecting different symbols/days.
- **Known L2 visibility limitation**: the inherited book starts with <=1000 bids/asks per side and accumulates later depth level changes, may contain stale levels outside current top-of-book. Therefore this pilot is **not sufficient to certify executable 10bps bid resilience**, order-specific cancellation, actual fills, or a marketable executable edge; monitor levels and exact-book snapshot diagnostics before considering any deployment.

## Source cost / artifact gates
Public repo `joseluisvieira28-oss/Laboratorio` verified 2026-11-23; standard `ubuntu-latest` public GitHub-hosted runner (currently free per official GitHub docs, with storage quotas). One GitHub `pull_request` DRAFT job, timeout **40 minutes**. No paid/larger runner, API subscription, persistent service, default-branch schedule, Render/Telegram, or change to main.
Raw source archive/ledger retained **7 days** as GitHub Actions artifact to limit free account storage; if archive expires before independent review, final status `MISSING_ARCHIVE`, no substitute. First-UTC-day pilot 2026-11-23 is NOT pooled as an independent day with existing BINANCE004/005 same-day studies. No recurring 010 automation is authorized until this first bounded source pilot demonstrates stability.

References:
- https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
