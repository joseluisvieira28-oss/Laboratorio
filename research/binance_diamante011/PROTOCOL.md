# BINANCE-DIAMANTE-011 — 30-MINUTE SEGMENTED LOSSLESS COMPRESSED SPOT L2 CAPTURE
**Registered 2026-11-24 UTC, BEFORE first BINANCE011 new market source observation.**
**Study identity:** `BINANCE011-FROZEN-004-30MIN-LOSSLESS-JOURNAL-V01`.
One isolated DRAFT GitHub PR. Source-only + frozen hypothetical L2 quote shadow. Zero orders, balances, private endpoints, API keys, user accounts, deposits, trade executions, payments, subscriptions, premium runners, production changes or merges to main.

## Basis and falsifiable question
Original frozen BINANCE004 (PR #375) 30sec sell aggression + visible 10bps bid-depth persistence + 60sec hypothetical LONG, extended to 30 minutes in BINANCE010 (PR #387). One 010 run #45186448917 captured 216,629 public WS frames + 3 snapshots and remained 3/3 SYNCED with exact book replay, but prematurely stopped at a pre-registered **220,000,000-byte raw JSONL journal cap** before completing 1800 seconds. **SOURCE_BLOCKED, NOT a profitable or unprofitable signal result.** 010 archive remains a failure and MUST NOT be relabeled or rerun.

011 attempts a fresh, separately frozen **2026-11-24 UTC** 1800-second Spot source session, retaining exact original UTF-8 `Journal.append` bytes and tamper-evident chain, while also writing rolling *independently decompressible* gzip chunks during arrival. No alternate source, symbol, fee or threshold; no reruns or rescue captures on same day.

## Original code identity, identical per-window science
- Exact files MUST match immutable Git blob SHA (do not modify originals):
  - `research/binance_diamante003/book_core.py` `9b2a92455d36dc251ec99a2754c07a7f91a9af91`
  - `research/binance_diamante003/capture.py` `490ad52bef283dedb4036e8793f6892788803a0e`
  - `research/binance_diamante004/PROTOCOL.md` `b1b8d2aa2b9dd4853e04671de0d96336ae895d1b`
  - `research/binance_diamante004/capture_forward.py` `ef8a987e026656cd3a60d402761c21078dee3ca7`
  - `research/binance_diamante004/study.py` `58cf6af9c0ba26da2ac9efa700c103b93c7580b5`
  - `research/binance_diamante004/verify_offline.py` `33ca9731cbbb2d4f22db8d5309d4616bfe3ca616`
  - `research/binance_diamante010/runner.py` `4c58e496c048e8a4d032cfcd022995fa20ba21b7`
- Source exact same six anonymous Binance Spot combined WS channels on `wss://data-stream.binance.vision`: BTCUSDT, ETHUSDT, SOLUSDT `@depth@100ms` and `@aggTrade`; 3 initial REST `data-api.binance.vision` `limit=1000` orderbook snapshots (one each), no reconnect or retries.
- Only operational change from 010: raw journal cap **220MB -> 520MB**, WS frame cap **250000 -> 420000**, lossless gzip **segment size <=16MB uncompressed**, total gzip bytes **<=160MB**, <=50 segments or archive fail. Exactly one full 1800-second session, **60 fully evaluated 30-sec windows per asset**, decisions until 1680sec, last 120sec reserved for 60sec maturity. Safety stop on source invalidity, cap, gzip CRC failure, broken hash chain, timestamp issue or unbridgeable U/u gap; preserve first failure with no substitution.
- Unchanged economic rule: sell-initiated quote volume >=5,000USDT per 30sec, sell share >=65%, visible 10bps bid depth end/start >=0.80, midpoint move >=-3bps, start/end book <2sec old, <=3sec after-decision entry next diff, 60sec exit <=3sec late; 120sec per-signal/type/symbol cooldown. Base/Stress costs 10bps taker per side +2bps or +5bps adverse slippage per side respectively; 100 and 1000USDT static orderbook walks, no actual fills; independent predeclared FLOW_ONLY and every fourth-window unconditional baseline. No rule optimization, no shorting.
- 003/004 original replay and economics are run against an *identical bit-for-bit uncompressed UTF-8 journal* reconstructed only for in-run science/replay. Gzip is **not a substitute for raw integrity**: every gzip chunk source decoded SHA256, gzip bytes SHA256, first/last record sequence, row-boundary fidelity, uncompressed total SHA256 and bytes; all gzip members re-opened, decompressed and compared byte-for-byte to the original journal BEFORE evaluating any signals. If raw journal exists only on ephemeral CI disk, do not upload it. On failure, do not infer economic NO_EDGE; upload remaining valid segment receipts and failure.
- Compression engine MUST implement a byte-identical tee of the original `Journal.fp.write(encoded)`: don't reserialize or reformat JSON, don't drop or resample frames, don't change clock precision, no separate threads changing arrival order. Verify offline equivalence in synthetic tests including at least 3 chunks, tampering and exact original chained records.

## Fresh 011 one-shot date / statistical independence
- One marker `research/binance_diamante011/requests/2026-11-24.txt`; `pull_request` workflow matches only isolated 011 branch and the exact UTC date. Prevent accidental multiple attempts on the same day. A 011 event is **not** pooled as independent with the 005 trial from the same UTC date if collected, nor with the blocked 010 November 23 trial.
- Public repo, standard `ubuntu-latest` only, 44min max runtime, no default branch schedule, no external paid storage, 7-day artifact retention. Gzip chunk total cap 160MB; if larger, SOURCE_STORAGE_BLOCKED; no automatic upgrade, premium storage or changing limits in same study.
- On CI event completion, remove ephemeral `journal.jsonl` **before upload**, even when the run fails, but preserve compressed original chunks, receipts and source-failure manifest. If gzip integrity fails, mark ARCHIVE_BLOCKED and do not claim source GO or economic PnL.
- If source completes and all hashes match, report source PASS and the **hypothetical** PRIMARY/FLOW_ONLY/UNCONDITIONAL_BASELINE maturity, positive-after-cost counts and 1000USDT stressed mean net bps, with original raw receipt SHA256. Any one-day result is categorically **ECONOMIC_INCONCLUSIVE / NO_LIVE_GO**, because original scientific gate needs >=200 primary matured trades across >=20 distinct UTC days, clustered bootstrap confidence, controls and independent replication.
- A lossless journal is necessary but not sufficient: original Binance 1000-level snapshot + diffs is not a globally complete order book and may accumulate stale/ghost levels outside visibility; no true order cancels/maker priority/market impact/fills can be certified. It does not resolve real-account trading fee eligibility.

## Source-only outcomes
- `SOURCE_BLOCKED`: incomplete 30min, transport or sequence gap, wrong UTC day, clock, frame cap or raw cap.
- `ARCHIVE_BLOCKED`: gzip cap, CRC32, chunk SHA, byte-for-byte reconstructed raw mismatch or missing part.
- `SOURCE_AND_REPLAY_PASS_ONE_DAY_ECONOMIC_INCONCLUSIVE`: full three-source 30m, 180 window, raw + compressed integrity, original deterministic book/quote shadow PASS, zero actual fills. **NO_GO_LIVE** in all cases.

This study is NOT a modification or rerun of BINANCE005/010; no merge, branch-only source evidence, no new scheduled recurring task.

References:
- https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
