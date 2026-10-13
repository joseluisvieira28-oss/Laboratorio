# CRYPTO LAB — PAYOFF 4R: FAILURE ECONOMICS + FUTURE SOURCE READINESS
Date: 2026-10-13 | Status: **RETRO_FAILURE_ATTRIBUTION_VERIFIED / PREENTRY_FILTER_NOT_ESTABLISHED / FORWARD_SOURCE_QA_PASS / SHADOW_NOT_RUNNING / NO_LIVE_GO**

## Immutable sources and receipts

- Base 2R–5R sweep [PR #195](https://github.com/joseluisvieira28-oss/Laboratorio/pull/195), GitHub Actions [38356035850](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38356035850), artifact **11792728776** with full event-level chronological ledger, source manifest and both fee scenarios, archive digest `sha256:d0febeb421ba2c69bca551bcb7838ea42baae5724b870e484ae4875a7d0523af`.
- Failure and pre-entry descriptors [Actions 38357962987](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38357962987) **SUCCESS**. Cost audit artifact **11793896023**; pre-entry source+feature artifact **11793731325**. Both run against already-observed, checksum-verified 2020–2025 Binance public source. No opened 2026 observations.
- Forward public-source mock [Actions 38358778991](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38358778991) **SUCCESS**, nine network-free mock tests for daily archive checksums, scope, 24-hour completeness, funding edge coverage, no private endpoint, window, future warmup. Does not prove real forward source availability.
- Original authoritative 4R frozen code `research/payoff_40_10_btc_001/engine.py` unchanged, no retroactive target or stop adjustments.

## Actual mechanism of losing years: frozen 4R BASE and Parent

Cash decomposition grouped by *exit year*, including historical Binance proxy taker fees (0.08% per side), modeled adverse 2bps fills and public historical funding. These are NOT authenticated MEXC cash flows and not account statements.

| model / exit year | closed | winners | gross price cash | fees | funding | final net cash |
|---|---:|---:|---:|---:|---:|---:|
| 4R / 2022 | 16 | 2 | −693.48 | −61.47 | −55.62 | **−810.57 USDT** |
| 4R / 2025 | 14 | 2 | −677.40 | −61.80 | −92.89 | **−832.10 USDT** |
| Parent / 2022 | 18 | 3 | −1,064.29 | −73.10 | −60.55 | **−1,197.95 USDT** |
| Parent / 2025 | 14 | 2 | −778.50 | −63.48 | −109.33 | **−951.32 USDT** |

All are historical open/closed events; not distinct independent prospective samples. Exit-year net cash is **not** equivalent to the strategy's year-by-year equity percentage because positions can cross calendar years, variable sizing and open holdings. 4R 2022 had 10 consecutive losses within the yearly exit cohort; 2025 6. BASE 4R 2025 median closed hold **158h**, Parent **45h**; 4R spent capital longer.

**Conclusion on causes:** losing price movements explain the bulk of the negative total in both years; neither zero fees nor ignoring funding would rescue those two specific exit-year cohorts. Yet funding is an important **tail-risk driver**.

## Funding can violate planned −10% margin loss by a lot

From immutable 4R BASE trade ledger: 81 total negative closed outcomes; **all 81 less than −10% of initial margin** after simulated costs. Seven fell below −12%, two below −15%, and one below −18%. The single worst margin outcome was **−19.515045%**, position entered **2021-03-28 13:00Z**, exited **2021-04-18 03:00Z**, held **20.5833 days**; initial hypothetical margin ~1,251.782 USDT; funding cash **−118.6315 USDT**, a **−9.477%** contribution measured against initial margin. Risk on whole equity at frozen 10% margin fraction was almost 1.95% for this isolated event, rather than the nominal 1%. This is not a guarantee of max loss from stops, mark-liquidation, spreads or gaps. The stop was reached but the actual net payout had already deteriorated through funding.

**The high-value improvement hypothesis is an *independent* funding-aware net-risk guard**, not a post-hoc redefinition of 4R. Candidate idea (not tested or approved): calculate at each bar the *future fee/slippage-adjusted net equity loss if stop executes*, including accrued funding, and adjust/close **before** projected −10%-of-initial-margin budget is exhausted. Trading execution / intrabar gaps can still exceed the cap. Such a rule changes exit times, future entries, and winners: it requires a distinct ID and fresh forward outcomes; no historical best-case claims.

## Pre-entry observations (descriptive only, no selected threshold)

For **4R BASE**, features at completed 1h bar *before entry*. Source: 221 checksum-verified public archives; 2022 entry cohort 17, 2025 14, other years 80; 0 missing descriptors.

| Group | SMA200 distance (%) | 20h return (%) | 20h daily-equivalent realised vol (%) | RSI14 |
|---|---:|---:|---:|---:|
| 2022 | +2.654 | −1.517 | 2.602 | 39.220 |
| 2025 | +2.042 | −1.260 | 2.033 | 40.243 |
| other 2020–2025 | +4.507 | −2.000 | 3.162 | 39.639 |

2022/2025 sampled entries tended to sit closer to SMA200 with lower observed 20h volatility. But within 2025, the loser/winner descriptor distributions overlap or vary counterintuitively (14 observations: **12 negatives, 2 positives by entry year**). No bin/threshold/volatility gate was preregistered or backtested, and no causal predictive power is demonstrated. **Do not now invent a volatility or regime threshold from these observed outcomes.**

## Operational improvement: prospective paired shadow source, but not enabled

Files:
- `research/payoff_failure_execution_forward/forward_public_daily_source.py`: no private API, no authenticated endpoints or trading actions. May only request Binance official BTCUSDT USD-M **daily** 1h market and mark archives with SHA-256 publisher CHECKSUMs; separate public fundingRate history; exact 24-hour date integrity and mark alignment; funding freshness / gaps must pass.
- `research/payoff_failure_execution_forward/forward_boundary_gate.py`: requires explicitly `PUBLIC_READ_ONLY_SHADOW`, 2026-10-14T00:00Z boundary, first 200 consecutive hours **exclusively after** that boundary as new warmup, last closed hour only, verified public funding + mark alignment, then compares original frozen 4R and Parent with BASE/STRESS without retuning.
- `research/payoff_failure_execution_forward/test_forward_public_daily_source.py`: network-free synthetic source QA passed by [run 38358778991](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38358778991).

**Schedule/readiness:** Binance states that daily public archives become available on the following day. With start 14 October UTC and 200h warmup, an intake ending at complete 22 October can first be attempted **23 October 2026** subject to published files and rate/API availability. The file is a prepared **one-shot script** on a research branch, not a running 24/7 service. The separate source QA workflow ran tests only. GitHub cron only works from a workflow located on the default branch; **no default-branch merge was authorized**. No automatic forward observations have been collected, no forward trade outcomes, no paper-trading micro-live GO. Existing parent V0.1/V0.2 forward authority remains unchanged and independent; do not count its old outcomes as this new block.

## Binary result + next authorized phase

- **Economic attribution:** PASS (known in-sample outcomes).
- **Proof that volatility or SMA200 proximity avoids losing trades:** NO.
- **Public prospective collector synthetic QA:** PASS.
- **Actual future collector verified on post-14-Oct official files:** NOT YET; future dates and 200h warmup not available at this audit date.
- **Exchange execution / hard risk cap:** NOT PROVEN: BBO bid-ask depth, actual taker fills, funding mark reconciliation on execution venue, isolated maintenance tiers, tick/lot, min notional, slippage shocks, downtime need binding.
- **Financial/live authority:** NONE. Research branch and draft PR only; main untouched.

**Recommendation:** preserve unchanged 4R and Parent in independent forward shadow first. Separately preregister a funding-aware *cash-risk budget* child **before new observations**, but do not use these old price paths as independent evidence. Do not trade real money on the retrospective +28.33%.
