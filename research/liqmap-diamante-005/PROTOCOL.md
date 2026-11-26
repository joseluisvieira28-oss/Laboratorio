# LIQMAP-DIAMANTE-005 — test of liquidation cascades as FUTURE VOLATILITY RISK, not direction
**Pre-registration 26 Nov 2026, BEFORE the first LIQMAP-005 source-outcome evaluation. Zero trading.**

## Scientific question
Does information in actually executed Hyperliquid liquidation episodes at the end of a completed hour improve the forecast of an unusually large BTC/ETH-PERP price excursion in the **NEXT four complete hours**, versus past price volatility alone? This is NOT a retest of the 004 directional NO-GO, nor Neuron's proprietary map. The source sample was previously explored in 004; the new hypothesis is retrospective, NOT true prospective OOS.

## Sources, fixed separation
- Reuse 004's read-only SHA256-validated Ironflow (ironflow.sh) Hyperliquid public Parquet: liquidation EVENTS (one per position liquidated) and same-exchange 1h OHLC; months 2026-07, 08, 09, 10. BTC-PERP, ETH-PERP only; no funds/accounts/wallet IDs shared.
- 123 calendar days, 2,952 contiguous 1h bars per coin; reuse 004 integrity checks, no substitution. Every time t represents completed hour t with known price and liquidation notional/count; no information from t+1 onward in inputs.
- **Training**: 2026-07-15T00:00:00Z to 2026-09-01T00:00:00Z exclusive. **Independent chronological reporting periods**: September then October; no threshold, fit or scaler modification after training. Neither constitutes genuinely independent *hypothesis formation* period, because past work inspected 2026 market; this is locked historical replication only.

## Outcome and controls — fixed PRIOR to evaluation
- At each hour t >=336, define maximum FUTURE excursion over 4 candles t+1..t+4 from entry reference OPEN[t+1]: max(max(HIGH[t+1..t+4]/entry−1), 1−min(LOW[t+1..t+4]/entry)). No stop/exit assumed; this is an OHLC-defined event.
- Define the t-relative HIGH-RISK label as future excursion >= the **90th percentile of 333 past 4-hour excursions ending no later than t**, indexed j=t−336..t−4 inclusive; same excursion rule with next 4 bars after j, all closed by decision t. Quantile nearest-rank method='higher'. If reference is zero or incomplete, BLOCK. Do not choose a fixed price threshold using future distribution.
- Baseline PRICE model uses only price-known-at-t: (1) abs(log(CLOSE[t]/CLOSE[t−4])); (2) sample std of 24 last hourly close log-returns ending t; (3) log(HIGH[t]/LOW[t]).
- Extended model adds EXACT two liquidation features: (4) log1p((liquidated LONG+SHORT USD in hour t)/(95th percentile of prior 336h total liquidation USD + 1)); (5) log1p(number of liquidated positions in hour t). Both are known only at END of t, no late event replay assumption.
- Two logistic regressions, sklearn StandardScaler fitted on training only, LogisticRegression L2 regularisation C=1, solver lbfgs, max_iter=1000, NO class weighting, fixed random_state 5005. No hyperparameter tuning, no feature selection.
- Primary: compare OUT-OF-TRAIN Brier score (lower better) on **October ONLY** extended vs baseline, report Sep as extra no-tune replication; log-loss and ROC AUC supporting diagnostics, event base rate, positive counts, and mean prediction.
- Bootstrap causal-dependence control: ISO weekly blocks across October, 2000 samples seed 5005, difference Brier baseline-extended (positive favours liquidation) with 95% percentile interval. No mixing BTC/ETH into independent n. October has ~5 calendar weeks and overlapping next-4h labels; CIs exploratory, not strong proof.

## Economic-utility countertest: fixed LONG vs CASH exposure
- Evaluate deterministic non-overlapping UTC-aligned 4-hour decision blocks (t.index % 4 == 0) in Sep and Oct, decisions frozen at t, invest 1x BTC/ETH-PERP only when predicted high-risk probability <=0.20; otherwise stay CASH (0%), using same cut 0.20 for BASELINE and EXTENDED; never short, never leverage, no optimization.
- Compare extended risk gate vs baseline risk gate AND passive 100% long, on same open t+1 to close t+4 4h not overlapping, with fee stress **10bps per side +5bps slippage per side** on each exposure change; a cash→long opening costs 15bps; long→cash closing costs 15bps. Fee stress also 35bps/side+5bps/side. The final position at end of period is hypothetically flattened at cost. Cash zero interest. This is ONLY approximate execution: next-hour-open idealized price, no real funding, spread, margin, fills, liquidation of trader, tax, vault or custody risks.
- Report total compounded NAV, worst close-to-close drawdown, exposure fraction, turnover, and monthly net profit. A risk predictor can lower losses in a down regime without any usable risk edge; compare to CASH and passive long.
- Do not change training, threshold 0.20, time range, costs, blocks or model specification after seeing results. Reject source gaps and future-price lookahead.

## Strict gates for **candidate to prospective SHADOW**, never real money
Both BTC and ETH must have >=500 October hourly observations and >=40 positive risk-label hours, Oct Brier improvement **>=0.005**, weekly-block bootstrap 95% LOWER bound of Brier improvement >0; improvement in September also >0; October long/CASH 15bps/side net NAV greater than BOTH BASELINE and PASSIVE, and max drawdown no worse than baseline, and >=2 independent month positive relative improvement. If any fail with sufficient sources -> NO-GO for liquidation ADDITIVE predictive feature; if sample too small -> INCONCLUSIVE. Even if candidate: no real trades, requires prospectively logged signals, actual account fees and extra independent history.

## Kill criteria
If 004 material integrity checks fail, if the events are not publicly accessible, if training contains one class only, or if price gaps, SOURCE_BLOCKED. If price-only baseline beats or equals cascade model in October, do NOT tune until it wins. The LIQMAP-002 scheduled prospective study is unrelated and untouched. No subscription, payment, trading, order placement, prod deployment, merge or extra automation.
