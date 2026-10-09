# RW-HL-EXITFLOW-001 — G2/G3 OBSERVABILITY ACTIVATION + SCIENTIFIC STATUS
Date: 2026-10-09; as-of ~19:55 UTC
GitHub branch: research/rw-hl-exitflow-source-first-2026-10-09
GitHub main: UNCHANGED
Trading authority: NONE

## Original distinct mechanism / provenance
Primary creator article: Kris Longmore / Robot Wealth, `Hyperliquid Carry Looks Trendy` (2025-09-14), https://edgealchemy.robotwealth.com/p/hyperliquid-carry-looks-trendy.
The author proposes that extreme negative Hyperliquid funding may mark informed/persistent pressure; rising OI concurrent with falling price is discussed as a possible way to identify it. **This is an economic hypothesis, not evidence of insiders, future PnL or actual market orders.** It differs from generic newly listed perp shorts only if venue-conditioned forward OI/funding mechanism and matched economic controls are later demonstrated.

The earlier projects already explored generic Binance launch short, launch basis convergence and derivative crowding interaction. Their exact identities remain closed/locked as documented in `audits/RW_HL_EXITFLOW_001_SOURCE_AND_ECONOMIC_FEASIBILITY_AUDIT_2026-10-09.md`. No prior hypotheses can be rescued by renaming.

## 1. G1 — no-cost public SOURCE PASS
- [GitHub run 37938587198](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37938587198): 14 synthetic tests PASS; two authenticated-free public `metaAndAssetCtxs` snapshots each of 178 validators' current perpetual markets; market-only OI, markPx, funding available.
- Exactly 24 BTC historical hourly funding records in one January 2024 day from public `fundingHistory`; historical open interest **NOT** present through this endpoint.
- Official historical `s3://hyperliquid-archive/asset_ctxs/YYYYMMDD.csv.lz4` requires requester-pays AWS egress; no expenditure and no AWS credentials requested. Dune/CoinGlass dashboards are not independently verified, no-cost, complete timestamp-pinned data exports. **2023–24 retrospective OI discovery remains HISTORICAL_OI_SOURCE_BLOCKED_NO_SPEND**.
- Official public documentation: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data ; https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals .

## 2. G2 — FROZEN SOURCE VARIATION PASS, NOT ECONOMIC
- Frozen BEFORE examining actual OI differences: `RW_HL_EXITFLOW_001_G2_SOURCE_VARIATION_FREEZE_2026-10-09.json`, commit `a2706a9ea352b1070b5c70704fc0b066119e31bc`.
- Source proof: immutable original [run 37939142048](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37939142048) three snapshots at 2026-10-09 13:45/13:46/13:47 UTC; recovery [37939670207](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37939670207) verified source byte hashes and SHA chain; no after-the-fact change.
- [G2 source-only census 37982161285](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37982161285): 19/19 synthetic tests PASS. 178/178 common markets, 178 positive OI, **159 OI changed**, 15 negative current funding at final snapshot, **6 co-occurring OI rising and funding negative**, 1 negative-funding sign flip. All five predetermined G2 SOURCE gates PASS. No price differences/returns or PnL opened.
- A two-minute raw OI increase cannot distinguish a seller from matched long exposure. Repeating the frozen G2 count over arbitrary favorable lookback windows or markets would be invalid.

## 3. GitHub source durability engineering
- First 3-snapshot transport [37939142048] completed API collection but encountered non-fast-forward Git commit race. Immutable source artifact preserved/recovered by [37939670207].
- V0.2 transport freeze and `git fetch/rebase` amendment made before the next prospective block. [Second 3-snapshot run 37982543077](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37982543077): 23/23 tests PASS, 3 genuine public snapshots of 178 markets at 19:46/19:47/19:48 UTC, now directly persisted on research branch; no force push/main changes.
- First G3 true-UTC-hour sample [37983025574](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37983025574): 13/13 tests PASS, one actual **2026-10-09 19 UTC** public OI/funding/mark snapshot of 178 markets. Source SHA256 `975005c205e56fc7dec26881bcf413341fcb0847a5816aa5de01276386f4bac2`. Raw file `research/rw_hl_exitflow/forward_source/hourly/2026-10-09/19.json`. Observations are source only and never filled retrospectively.

## 4. Hourly task ACTIVATED and source-only 14-day freeze
- An hourly condition-watch task `Hyperliquid Exitflow Forward` was created in ChatGPT on 2026-10-09 19:52 UTC and confirmed enabled; it checks source identity and recent workflow runs, triggers exactly one genuine current-hour capture when absent, and notifies only scientific/operational milestones.
- A source-only immutable activation contract `RW_HL_EXITFLOW_001_G3_SCHEDULER_ACTIVATION_2026-10-09.json` was frozen **before any 2026-10-10 evidence**. Window = **2026-10-10 00:00 through 2026-10-24 00:00 UTC EXCLUSIVE**. **336** prospective hour slots; minimum **320 unique actually received hour receipts**, **14 UTC dates**, at least 100 valid markets in >=95% samples, zero data conflicts. Missed timestamps remain MISSED, not fabricated. Oct09 pilot not counted.
- G3 source-only `rw_hl_g3_coverage_adjudicator_v01.py` + 14 synthetic tests PASS, [run 37983428415](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37983428415); present classification **G3_FORWARD_INSUFFICIENT_UNTIL_2026_10_24_UTC** (correct because the frozen window has not begun yet).
- Terminal G3 quality assessment will be triggered ONCE by `research/rw_hl_exitflow/G3_COVERAGE_AUDIT_TRIGGER.txt` after the window closes; its frozen outcomes are `G3_SOURCE_COVERAGE_PASS`, `G3_SOURCE_COVERAGE_BLOCKED_OR_INSUFFICIENT` or `G3_SOURCE_INTEGRITY_BLOCKED`. These are SOURCE gate labels, NOT economic PnL judgments.
- The source task is recurring on the ChatGPT automation service, **not** a fake GitHub Actions `schedule` in the nondefault branch. Best effort scheduling has no guarantee of 100% uptime; coverage gate will expose any omissions.
- GitHub repository is currently PUBLIC; source workflows use standard `ubuntu-latest` hosted runners, which GitHub documents as free for public repositories. Artifact storage may still be quota-limited; no larger paid runner, S3 or paid data was used. https://docs.github.com/en/actions/reference/runners/github-hosted-runners

## 5. Economics unchanged, NOT TESTED
- Hyperliquid official base perpetual taker 0.045%/fill = **4.5 bps/side**, so a single short opened/closed via taker route pays **9 bps before spread/slippage**. Maker 0.015%/fill nominal base, passive fill/queue and adverse selection unproven. HIP-3/tier/staking discounts may vary and are NOT assumed. https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- Funding is settled hourly. **Negative funding makes shorts PAY longs**. Realized settlement funding must be bound to the period and underlying oracle; current instantaneous funding indicator cannot be substituted for actual historical funding payments. https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
- A separate **G4 pre-outcome numerical signal/economic freeze** must be committed before reading any post-signal price returns. Require prospectively timestamped OI growth, market/benchmark trend, true listing T0 if claiming new listings, fixed eligible cohort, matched controls, venue BBO/execution/funding, fees, slippage, capacity, squeezes, sample floor and confidence intervals. Neither G1, G2 nor G3 alone gives trading authority.
- Do not infer profitability of any suggested Robot Wealth technique; author's reported factor examples are not user-account audited post-cost executions.

## Terminal classification AS-OF NOW
`G2_SOURCE_VARIATION_PASS_NOT_EDGE` + `G3_FORWARD_INSUFFICIENT_UNTIL_2026_10_24_UTC` + `HISTORICAL_OI_SOURCE_BLOCKED_NO_SPEND`.
Scientific economic verdict = **NOT TESTED**, not NO_EDGE or SURVIVES.
No orders, live trading, account/wallet access, paid data, exchange mutation, main merge, Render deployment, price outcomes, OOS leakage or retuning.
