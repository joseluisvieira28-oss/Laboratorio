# CRYPTO LAB — TRADINGVIEW DIAMOND HUNTER V0.1
Date: 2026-10-14 UTC
State: DISCOVERY_SOURCE_METADATA_ONLY / ZERO_PINE_SOURCE_AUDITED / ZERO_NEW_MARKET_OUTCOMES / NO_LIVE_GO
Authority: user's 2026-10-14 request to hunt external public TradingView ideas. Science-only; no exchange access, paid services, wallet, live orders, merge to main, 2026 sealed holdout opening, or retuning failed historical designs.

## Mission
Seek a materially distinct, causally implementable futures mechanism with materially more trades than SOL 1h (84 closed/2023-25) or BNB 4h (28 closed/2023-25), positive base AND stress after realistic complete round-trip fees, adverse slippage, spread, funding, latency, gap fills and venue constraints. **Trade frequency alone is neither edge nor authorization.** Do not estimate a strategy's trades, edge, win rate, or annual income from TradingView page descriptions.

## Existing repository evidence / negative controls
- SOL1h 2023–25: +59.39% BASE, 84 closed, PF 1.824; BNB4h +27.38%, 28 closed, PF 2.894. Already examined historical price data; not independent OOS. Sources: PR #215, audit/convex-8alt-common-2023-25-2026-10-13.
- FAST-CONVEX V1 frozen 8 alts x 4 TF x 2 hold x 2 cost: 128/128 historical after-cost losses, even high frequency SOL 5m/8h ~2011 trades lost ~48% BASE. Source: PR #220. No post-hoc target/stop salvage.
- SHORT-REJECTION-SCALP-001 frozen eight assets: all negative including all 8 static fee-free ledger sensitivities; source PR #219. New sweep/rejection idea must show MATERIAL causal distinction, not merely fresh names for old rejection.
- BTC-CONVEX 1h retrospective +15.07% BASE 2021–25 but heavy funding/winner concentration; PR #212/#213. No guarantee.
- OPTIONS V2.1 MARKET/MARKET 10x live NO-GO; PR #202. Leverage cannot create edge.

## TradingView public-source intake — independently identified pages (NOT vetted Pine source)
| Priority | Source page; publication metadata | Described economic mechanism | Duplication / failure risk | Gate |
|---|---|---|---|---|
| P1 | HV Spike Strategy, kostastrovas, 2025-10-26, https://www.tradingview.com/script/1oZNa7Oq/ | HVP/historical-volatility percentile selects first high-volatility reference bar, follow-on range breakout or reversal, percent/ATR exits | Parameter selection by coin explicitly promoted in description; intrabar breakout timing, same-bar fill and overfit concern; need fully different entry vs prior FAST V5 | SOURCE_CODE_REQUIRED |
| P2 | @santoshpsiii Crypto Algo, smvdtravelsolutions, 2026-05-19, https://www.tradingview.com/script/9x9ohJ2R/ | BB width regime > baseline then SuperTrend flips 5m/15m, both directions | Churn/reversal fee drag; overlaps familiar momentum regime logic; simplistic indicator confluence | SOURCE_CODE_REQUIRED |
| P3 | Stratégie SMC V18.2 BTC/EUR, rico2956, 2025-11-28, https://www.tradingview.com/script/ZyPd3ENh/ | 15m sweep + BOS + order block with 1h EMA trend; 1:3 RR advertised | SHORT-REJECTION 90m negative; BTC/EUR spot symbol versus target futures; higher timeframe lookahead; self-reported PF claims NOT accepted | SOURCE_CODE_REQUIRED / DUPLICATION_REVIEW |
| P4 | Crypto Volatility Bitcoin Correlation Strategy, exlux, 2024-10-05, https://www.tradingview.com/script/B0skL3uT/ | VIXFix + BitMEX BVOL7D + EMA trend | External series historical contemporaneous availability, release timing, cross-symbol revisions; likely fewer trades; check whether source is actually open and executable | DATA_SOURCE_GATE_REQUIRED |
| P5 | Master Strategy BTC W1 Mean Reversion, TheMrD, 2025-12-25, https://www.tradingview.com/script/vDtK5OfB/ | Weekly range stop sweep + 4h reclaim + limit-entry targeting mid-range | Indicator not directly testable as strategy, low likely frequency, limit-fill survivorship, previously failed rejection analogue | DEPRIORITIZED_PINE_REVIEW |

TradingView metadata pages are public, but full immutable Pine source, inputs, version ID, calculation modes, exact fill rules and trade reports have **not** been acquired through the available read-only tools. The site's rendered page text shows descriptions, not a complete source listing. No source claim is inferred merely from the OPEN-SOURCE label. No TradingView automation, scraping or bypass is used.

## Pre-code gates (fail closed)
S0 SOURCE: Obtain exact script Pine text directly by permissible manual export, script URL/title/author/version or update timestamp, originally displayed defaults, script kind (indicator vs strategy) and copyright/license. Record SHA256 over exact bytes; license review before storing third-party source in public repo. Prefer storing only SHA/hash plus commentary and keeping shared text in conversation if license uncertain.
S1 CAUSAL CODE: Independently inspect request.security / lookahead_on / security higher-timeframe close; pivot confirmation; barstate.isconfirmed; strategy.entry/exit intrabar assumptions; process_orders_on_close, calc_on_every_tick, calc_on_order_fills; limit orders and bar magnifier; repaint/revision; imported libraries and webhook execution semantics. Static grep is NOT a proof of no repainting.
S2 DISTINCT FAMILY: Compare mechanism to existing FAIL closes and prior trend/reversion families; no renaming/fresh stop parameter after outcomes of existing samples.
S3 MARKET SOURCE: Require independent checksum-verifiable price and, as necessary, external volatility/OI/mark/funding from time-of-availability. All gaps SOURCE_BLOCKED, never fabricated or filled to save results.
S4 ECONOMICS: Before reading market results freeze symbols, TFs, directions, state machine, order fill assumption, funding marks, entry latency, a realistically justified trading cost BASE+STRESS and gate thresholds; no strategy retuning on already-viewed price years. Futures-only simulated one-slot ledger and matching unit exposure to compare with parent.
S5 CONTROLS: No-lookahead unit tests, independent signal replay, 1-minute/5-minute resolution as necessary, pessimistic stop-first collision, same-bar orders forbidden unless witnessed real quote; delayed entry and placebo controls, year/regime breakdown, top-three winner concentration, drawdowns and 3 years uniform coverage.
S6 INDEPENDENT SCIENCE: Historical 2023–25 was already examined extensively in Crypto Lab and is descriptive for our team; **do not call an overlapping replay OOS**. Preserve the 2026 protected holdout. New genuinely prospective witness/quotes must be frozen before source/outcome collection, and independent robustness assessed before any promotion.
S7 EXECUTION: Venue-compatible min order, bid/ask executable quote, spread, slippage, user fee tier only after explicit permission, margin, funding and liquidations, safe protective stop and restart/reconciliation; source-only order book snapshot does not mean order fill. No live authority.

## Preferred first-pass decision
P1 HVP breakout is the first priority to source, because it frames a different regime-conditioned event from old V5 LONG signals. P2 is a lower-confidence quick frequency challenger; P3 only on explicit mechanism-difference proof; P4 waits external BVOL causality/source; P5 unlikely to outperform SOL1h on frequency. **These are research-priority judgments, not performance rankings**.

## Exact assistance needed from operator
1. From https://www.tradingview.com/script/1oZNa7Oq/ click Source code or add script to chart > Pine Editor > Source code; share full source as .txt/.pine (include first license line and script version), plus screenshot of default Inputs and Properties. No password/API/token, no account login delegation.
2. If possible also https://www.tradingview.com/script/9x9ohJ2R/ same materials. If any is Protected and no source is offered, say so; we will stop Pine-exact audit for it rather than reverse-engineer or pretend equivalence.
3. Optional Strategy Tester/Strategy Report > List of trades CSV and Performance CSV as separate files **with chart ticker, venue, timeframe and date range**. These are supporting falsification evidence, never substitute for causal independent replay. No subscription required or recommended.
4. Actual MEXC account fee tier or trade receipts can be discussed later if necessary, but DO NOT share private credentials. For now test conservative published fee/slip models unchanged.

## Outcomes / actions
- Public descriptions checked and cross-referenced against frozen repo reports; priority register and fail-closed protocol created on isolated branch only.
- 0 complete third-party Pine scripts acquired, 0 new historical trials, 0 positive profits, 0 genuine forward candidates promoted.
- Next legitimate step is exact Pine source S0 then independent causal reproducibility, not launching trades.

## Audit references
https://github.com/joseluisvieira28-oss/Laboratorio/pull/215
https://github.com/joseluisvieira28-oss/Laboratorio/pull/220
https://github.com/joseluisvieira28-oss/Laboratorio/pull/219
https://www.tradingview.com/pine-script-docs/concepts/strategies/
https://www.tradingview.com/support/solutions/43000614705-strategy-produces-unrealistically-good-results-by-peeking-into-the-future/
https://www.tradingview.com/support/solutions/43000613680-how-to-export-strategy-data/
https://www.tradingview.com/support/solutions/43000590599-script-publishing-rules/
