# MEME-DIAMANTE-002 — freeze 2026-11-18

Status: RESEARCH GO / ECONOMIC NO-GO. Read-only; no wallets, funds, API keys, orders, signing or payments.

## Hypothesis (unproven)
After a >=28% drawdown from an as-of peak, a >=12% bounce from the as-of trough backed by distributed buyer addresses and liquidity could predict costed tradable upside. Multiple addresses are NOT proof of independent humans (Sybil/bundle risk).

## Fixed parameters
- Signal age: 180 to 3600 seconds from first witnessed print.
- First peak-to-trough drawdown >=28%; bounce >=12%; current price <=95% of as-of peak.
- Previous 300 seconds: >=8 buy addresses with >=$50 each; >=$1,200 total buy; buy volume share >=65%; biggest address share <=35%.
- Current observed liquidity >=$20,000; trade size $100 hypothetical.
- First eligible entry print 30-120 seconds after signal; if absent = ENTRY_UNOBSERVED.
- Exit at first trade touching -25% stop / +30% profit, or first trade after 30 minutes. Missing exit = EXIT_UNOBSERVED; missing liquidity = BLOCKED, not a winning trade.
- Illustrative roundtrip costs: each side 1.70% + 2% slippage; $0.10 fixed. Test sensitivity at 0.5/1/2/5% slippage, different venue fees and failed orders.
- Event timestamps must be audited against actual data availability. NEVER substitute future historical prices for available contemporaneous quotes.

## Data and evaluation
- Required: whole Pump.fun creation universe including tokens that never trade/migrate, raw trade timestamps and availability timestamps, mint/pool, signature, buyer/seller, sizes, price, liquidity, traceable original responses and hashes.
- First 30 calendar days prospective; a target of >=200 qualified signals; NEVER tune on held-out days.
- Compare no-trade, momentum-only and age/liquidity/day matched randomized entries, with identical entry/exit/cost assumptions.
- Marketable quotes, fill feasibility, priority costs, MEV exposure and exits must be independently verified; prints are optimistic proxies.
- Bootstrap confidence intervals clustered by DAY, tail risk/drawdown, coverage, missing exits and regimes.
- Economic GO requires positive out-of-sample conservative net expectancy with positive lower confidence bound, outperforming controls and defensible execution. All other states = NO-GO or inconclusive.

## External baseline: NOT a strategy backtest
https://pumpdata.fun/public/baserate.json : on 2026-11-17, 1,688 token first crossings of 15k-28k USD capitalization; within next 3 hours, 35.1% touched 2x, 10.7% touched 5x. These are future *maximum touches*, not executable returns. Vendor data, independent verification needed.

## Sources
https://pump.fun/docs/fees
https://github.com/git-disl/MELT (41,470 migrated tokens; survival selection; CC BY-NC 4.0)
https://www.bitquery.io/datastore/datasets/pumpfun
https://api.geckoterminal.com/docs/index.html
https://docs.dexscreener.com/api/reference

## Blocking reason
No complete raw historical/forward trade data with observation timestamps and independently marketable quotes in this PR. Unit tests with synthetic trades DO NOT show an edge. **NO-GO live trading.**