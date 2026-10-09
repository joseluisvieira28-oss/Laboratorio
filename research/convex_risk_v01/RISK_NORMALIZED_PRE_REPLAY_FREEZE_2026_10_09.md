# BTC CONVEX — PRE-REPLAY RISK/NORMALIZED ALL-BASKET ECONOMIC FREEZE V0.1
2026-10-09. New research family / counterfactual risk redesign. This freeze is published **before running this new risk-normalized historical replay**, but the source outcomes are **already known**. Not a new independent OOS/holdout or a pre-outcome freeze of 2021–25 market behavior.

## Original data identity, fixed ex ante for this diagnostic
Immutable existing original 2021-01-01→2025-12-31 trade+fees+funding ledgers: GitHub Actions runs 35918769969 / 35921780080 / 35956632021 and respective artifacts 10775714534 / 10778258822 / 10791006099. Exactly 13 original Parent V5 instruments: FIRST ETH/SOL/BNB; EXPANSION XRP/DOGE/ADA/LINK/AVAX; THIRD LTC/BCH/TRX/DOT/UNI. Parent trades in H2 third experiment, not H2 child, must be used for common risk replay; separately report H2 original FAIL, no hindsight switching.
Use both BASE and STRESS original-cost layers; do not remove original losses or change signal, RSI, z, stop/trail, horizons, exchange or detector.

## New risk engine parameters locked before replay
Initial counterfactual capital: 10,000 USDT, one shared portfolio. Independent per-asset 10,000 USDT replay is a secondary diagnostic.
Original planned stop: 4% of filled notional; frozen BASE commission 0.10% per side and BASE 0.02% slippage per side ⇒ planned approximate stop+roundtrip drag=4.24% of notional, before funding/gaps. **This is a risk planning denominator, NOT a stop-loss guarantee.**
Test **both** planned risk levels PER position: 0.25% and 0.50% of current realized shared-account capital at entry (notional fraction = 0.0025/0.0424 or 0.005/0.0424 respectively), capped at 95% of equity.
Portfolio position policy fixed: at most 3 concurrent trades, aggregate planned risk reservations at most 1.00% of capital at each decision. Process exits before entries at the exact same timestamp; process simultaneous entries in lexicographic symbol order; skip (log) excess-risk signals **without substitution or rescheduling**. Positions are held exactly for original trade's entry→exit period, and payoff per notional including original funding+fee is net_pnl/(original qty*original entry). No invented orderbook fills.
Do NOT leverage, double-count funding, or assume same nominal equity per asset in the shared portfolio. Normalize fees and funding per original notional.

## Four prespecified evaluations
1. SOLO: all 13 exact Parent assets separately under .25% / .50% risk and BASE/STRESS, compounding trade-level (not bar MTM) PnL.
2. FIRST basket: ETH/SOL/BNB shared portfolio. SECOND: XRP/DOGE/ADA/LINK/AVAX. THIRD: LTC/BCH/TRX/DOT/UNI. ALL13: all symbols without cherry picking.
3. Cost sensitivity: BASE, original STRESS, and `BASE_PLUS_20BPS_ROUNDTRIP`, subtract additional exactly 20 bps net of entry notional on **every** trade, positive or negative. It is a synthetic adverse friction scenario, not independently observed cost. No lower fee alternative or rebates.
4. Tail survival: deduct **three original greatest BASE winning trades PER ASSET** from the opportunity set before constructing portfolios; re-run chronological risk engine on remaining trades and record skipped IDs. Selection is *adversarial hindsight removal*, not an implementable strategy or independent prospective evaluation. Confirm effect on profits and drawdowns. Also report worst single net normalized return, cumulative annual net and missed signals because of risk concurrency.

## Report metrics and integrity
- SHA256 each exact source archived ledger, original universe/timeframe and chronological trade data count, no overlaps per asset or NaNs.
- Each portfolio: completed trades, skipped overlapping due to shared exposure, equity/net-return, realized-only drawdown, profit factor, win rate, average win/avg loss (new scaled portfolio PnL), maximum losing streak; annual portfolio realized PnL in dollars; positive years; largest winner share. Every risk/no fill caveat explicit.
- For no intra-trade marks available, **realized-only drawdown is understated** vs full open-position mark-to-market. It may NOT replace original 54–59% original high-exposure bar MTM DD. Equity at each entry is cash-equity excluding unrealized PnL; no account liquidation/margin modeling.
- Do not infer retail min contract, MEXC access, actual fills, funding-transfer parity, slippage stochasticity, post-2025 behavior, or live profitability from archived trades.

## No retroactive rescue
The first basket local HISTORICAL_SCIENCE_PASS_SCOPE_LIMITED and second expansion/global FAIL remain unchanged by this new exposure experiment. Do not promote only ETH/SOL/BNB as an independently **new** winner; their results are previously seen. If lower risk reduces DD, that's mechanical capital scaling, not restored economic edge. H2 original 1/5 gate fails regardless of new sizing.
This experimental decision needs **no future event observation**; report HISTORICAL_RISK_SCENARIO_VALID or FAIL as appropriate. No live trading/account/private exchange/money/wallet/orders, no main merge, no alteration of original freezes or protected outcomes.
