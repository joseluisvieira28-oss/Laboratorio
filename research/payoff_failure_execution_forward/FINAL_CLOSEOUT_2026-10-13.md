# CRYPTO LAB — BTC PAYOFF 4R: FAILURE / EXECUTION / FORWARD CLOSEOUT
13 October 2026 | PR #196 | RESEARCH-ONLY / ZERO PROMOTION

## Final state
- **Historical attribution: PASS** (CI run [38357962987](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38357962987), jobs cost_attribution + preentry_regime_description both SUCCESS).
- **Pre-entry source/feature audit: PASS** on exactly 2020–2025 verified source, 2026 barred; no feature-based strategy retuning.
- **Public read-only future source & safety gates: CODE STAGED**, never a trade executor. Strict 2026-10-14 00 UTC boundary and >=200 post-boundary warmup; synthetic QA tested. **NOT CURRENTLY RUNNING 24/7**, no automatic scheduler enabled. New prospective market outcomes: **ZERO checked**, thus no forward edge evidence.
- **Execution: PARTIAL/NOT EXCHANGE-PROVEN**. Binance USD-M public prices and official historical funding proxies, assumed fees & slippage. Actual MEXC BBO, personal fee tier, fill probability, min order and historical margin/liquidation tiers not established; NO MICRO-LIVE GO.

## Independent existing evidence / reproducibility
Source: [PR #195 run 38356035850](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38356035850), canonical artifact #11792728776, SHA256 archive `d0febeb421ba2c69bca551bcb7838ea42baae5724b870e484ae4875a7d0523af`. This closed trade ledger was already exposed to analysis, not new OOS. Artifacts from PR #196:
- Cost attribution ZIP #11793896023, SHA256 `07864b9ba1a0e0b5dee7e9c437b4909415ad4c2f2cab7d4671b8dc76cdcf81a2`.
- Pre-entry features ZIP #11793731325, SHA256 `25914991d752b9762bcad67c49e0d3c156a9cf4f8805e958317e96f7529a714f`.
- Full per-trade and per-entry/exit-year breakdown: `FAILURE_AUDIT.json`; prior closed / mark-to-market performance remains PR #195, unchanged.
- Pre-entry descriptive evidence: `PREENTRY_DESCRIPTIVE_ONLY.json`, with 221 checksum-verified public-source request manifests in `SOURCE_MANIFEST.json`. Zero missing signal-bar observations for analysed closed-trade entry years.

## Why 2022 and 2025 lost money — BASE, grouped by exit year

| Historical model | 2022 exits | Winners | Gross synthetic price PnL USDT | Total modeled fees USDT | Modeled funding USDT | Net modeled cash USDT | Worst consecutive losses within year | Median holding hours |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PAYOFF 4R | 16 | 2 | -693.48 | -61.47 | -55.62 | **-810.57** | **10** | 76 |
| PAYOFF 4R 2025 | 14 | 2 | -677.40 | -61.80 | -92.89 | **-832.10** | **6** | 158 |
| PARENT 2022 | 18 | 3 | -1064.29 | -73.10 | -60.55 | **-1197.95** | 7 | 51.5 |
| PARENT 2025 | 14 | 2 | -778.50 | -63.48 | -109.33 | **-951.32** | 8 | 45 |

The first column's labels for 2025 indicate the analogous exit cohort; 2022 row for 4R and 2025 row are **different** groups, not consecutive annual percentages. Gross synthetic price PnL uses adverse-slippage fills already. Funding is modeled from public Binance historical rates, not from user's MEXC account. Annual equity percent returns from previous closeout differ from these dollars because of equity compounding, cash timing and cross-year trades.

**Inference limited:** price outcomes in the actually simulated trades are the largest negative contribution, so making trading fees 0 cannot rescue these historical cohorts alone. This doesn't prove an actual profitable "bad-regime" entry filter.

## Pre-entry descriptors — all observable at preceding confirmed hourly CLOSE

Cohorts below are by **entry year**, not exit year, thus different Ns from table above:

| PAYOFF 4R entry cohort | Entries | SMA200 distance % | Prior 20h price return % | Prior 20h daily-equivalent realized vol % | RSI14 |
|---|---:|---:|---:|---:|---:|
| 2022 | 17 | +2.654 | -1.517 | 2.602 | 39.220 |
| 2025 | 14 | +2.042 | -1.260 | 2.033 | 40.243 |
| 2020/2021/2023/2024 | 80 | +4.507 | -2.000 | 3.162 | 39.639 |

**What is observed:** the weaker historical years had smaller average above-SMA200 distance and lower recent realized volatility on these specific entries. RSI differences small. These are **group means**, not a legitimate success predictor.

**Adversarial within-year counterexample:** in 2022, the two positive 4R trades started at average SMA200 distance **+1.446%**, whereas losing trades averaged **+2.913%**; in 2025, positive trades averaged **+3.196%** against losing trades **+1.850%**. The direction of separation **reverses** between years. A simplistic higher-SMA200-distance filter tuned to 2025 might have suppressed the two 2022 winners, and vice versa. For prior realized volatility, 2022 winners averaged **2.018%** vs losers **2.727%**, another warning against assuming high-volatility improves this strategy. Tiny group sizes preclude confident predictive statements.

**Action:** NO new regime threshold/filter, no retrofitting. Record fixed descriptive fields prospectively and compare on clean forward observations. Don't hunt another backtest winner in this same source.

## Execution and risk gaps still open
- Historical full source uses **Binance BTC perpetual proxy**, not verified MEXC futures fills. Same nominal price barrier and margin do not guarantee same realized +40%/−10% on another venue.
- Slippage 2/5 bps per side is *assumed*, not venue bid/ask depth; sensitivity isn't proof of order fill reliability, especially around stop gaps.
- BTC 2x isolated maintenance threshold is only a proxy; exact liquidation mark semantics, historical min lot/tick and account risk mode are unverified. Unfilled stops/gaps can exceed −10% initial margin and 1% hypothetical account.
- Long holds increase funding and capital tied up; 4R median hold 2025 exit cohort **158h** vs PARENT **45h**.

## Forward staging
- Frozen source protocol: `PROSPECTIVE_SOURCE_ACTIVATION_FREEZE_2026-10-13.md`.
- Source-only public downloader `public_future_source.py` contains only public HTTPS GET paths, hard-fails before 2026-10-22 10 UTC minimum completeness for 202 after-boundary bars (earliest signal after >=200 warmed hours), no 2026 preboundary candles.
- `forward_boundary_gate.py` rejects earlier data, incomplete bars, missing mark coverage and unverified funding query range; replay must use only post-boundary market/cost records and unmodified PARENT/4R engine; source still must prove Binance quote/mark semantics and later venue compatibility.
- Manual workflow `payoff-forward-public-manual.yml` can be triggered by a **future commit** to `research/payoff_failure_execution_forward/control/run-*.txt` on this research branch. Workflow_dispatch on nondefault branches may not be available; push trigger is explicitly provided. Trigger file NOT committed, so collector is **not currently executing**. A branch GitHub Action schedule is not a functioning 24/7 cron. No autonomous monitoring or prospectively measured trades claimed.
- No source called for post-boundary economic results in this mission. The next legitimate phase starts only after >=202 complete post-boundary public hourly bars, prior committed source freeze, run receipts, no science-tuning, and verified operational runner.

## Decision
**Failure mechanism partially identified: many stop losses and weaker price moves in 2022/2025; fees/funding exacerbate but aren't sole causes. A single ex-post trend/volatility filter is NOT justified.**
The best next scientific step is independent future collection with the original 4R + Parent rules, plus real venue-execution feasibility. All historical numbers have **zero independent promotion credit**. The original PR #194/#195 science remains untouched; no main merge, trading, orders or spending.
