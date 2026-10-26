# FUSION RADAR HISTORICAL TRIAGE V0.3 — FROZEN EXPLORATORY DESIGN
Date: 2026-10-26. Branch: research/fusion-radar-three-panels-v02-2026-10-25. Related draft PR #271.
Status: HISTORICAL_DESIGN_REGISTERED / NOT_RUN_ON_AUTHENTIC_MARKET_ARCHIVES / NO_ECONOMIC_PROMOTION.

## Question
Does the causal, already-recognized BTC 20-day trend *context* improve the average net outcome of an AVAX 20-day directional price-state proxy, compared to the exact same AVAX proxy without that context?

**This is not a reconstruction of the original CED1D-0031 H1 alpha or the full multi-family Fusion.** It is a distinct, low-resource negative-triage child. The historic period and original member families have been investigated before. Even a positive historical result is EXPLORED_ALREADY_EXPOSED_DATA, never independent OOS or genuine validation of Fusion.

## Immutable scope before first new run
- Calendar: 2022-01-01 inclusive to 2024-01-01 exclusive, UTC only. Warmup includes 2021-12. ALL of 2024/2025/2026 forbidden for this exploratory runner.
- EXACT public archive source: Binance Vision BTCUSDT Spot 1D; AVAXUSDT USD-M perpetual 1D plus 1H. Monthly archive ZIPs, one CSV each, official sibling CHECKSUM SHA256. Fail closed on unavailable/invalid month, duplicate, malformed timestamp, incomplete required causal bars, unexpected calendar or wrong venue.
- For each day D at 01:00 UTC, direction AVAX = sign(close[D-1]/close[D-21] - 1). BTC context = sign(BTC spot close[D-1]/close[D-21] - 1). Flat AVAX -> no trade; flat BTC -> no Fusion vote.
- No interpolation, no post-outcome lookback/asset/threshold optimization. Signal uses completed bars only. Binance archive publication/revisions may occur long after historical D; historical live receipt/quote is NOT attested.
- Both hypothetical variants enter reference AVAX futures 1H OPEN at D 01:00 UTC, exit reference 1H OPEN D 02:00 UTC; 01:00 follows previous day's close. These are proxy prices; neither point is a proven executable fill.
- Baseline: every nonflat AVAX state enters as long/short. Fusion: exact same action ONLY if BTC20 agrees with AVAX20, otherwise FLAT (zero modeled fees). Prespecified falsifier: inverted BTC20 context, used as descriptive negative control, NOT optimized alternative. No reallocation or leverage.
- Economics: single unit notional exposure on an eligible day; BASE 14bps and STRESS 20bps hypothetical roundtrip friction, applied only to entered days; no funding/mark/slippage beyond cost assumption, account/access/collateral, liquidation, trading permissions, spreads or execution proof. Same values across all arms. Do not infer parent CED results from this proxy.
- Predeclared report: N trades, mean net bps PER CALENDAR DAY (primary descriptive comparator), mean net PER TRADE (secondary, selection-biased if alone), net PF, percentage profitable net trades, summed noncompounded net bps on one daily unit notional, cumulative-bp drawdown proxy, and yearly 2022/2023 diagnostics. If source fails, NO_REPORT / SOURCE_BLOCKED rather than zeros.
- Main comparison: Fusion minus baseline in mean net bps per calendar day under both costs. Prespecified falsification: if Fusion does not outperform baseline under STRESS20, this exact filter receives no further investment. If positive, still NO_EDGE because data is exposed, selection multiplicity is material, timestamps/real execution unproven and no independent block.
- No automated CI/download without explicit new workflow. The separately delivered Windows ZIP contains local reference implementation with --fetch as explicit manual GET mode and synthetic tests. This branch's registered scope is not a claim that code was committed to GitHub.

## Governance
No trading, authenticated/private API, wallet, balance, money, new service, deploy, Render, Telegram, Windows mutation, protected data, strategy stop/rule changes or merge to main. Do not re-interpret CFTC and BNB events from candles. To evaluate their effects historically, separately freeze their authentic as-of announcement/release series, original exposure decisions and fixed benchmarks; price-only files are insufficient.

## Sources
Binance public archives: https://github.com/binance/binance-public-data/
Legacy Crypto Lab research PR #141 (primitive map), #162 (ensemble governance), #203 (retirement), #271 (Fusion scope), #265 (CONVEX caveats). Historical Binance raw archive hashes must be recorded in every eventual real-source receipt.
