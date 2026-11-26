# LIQMAP-DIAMANTE-005 — INDEPENDENT SCIENTIFIC / ECONOMIC VERDICT
**26 November 2026 | SOURCE PASS | 6/6 TESTS PASS | ADDITIONAL LIQUIDATION RISK FEATURE: NO-GO | LIVE CAPITAL: NO-GO**

## 1. Original objective and frozen experiment
After LIQMAP-004 found no profitable directional cascade effect, LIQMAP-005 asked whether executed liquidation volume/count can predict *NEXT 4h unusual excursion / volatility risk*, **beyond a price-only model**, and whether a simple risk-aware LONG/CASH policy improves its net result.
- Pre-registered in research/liqmap-diamante-005/PROTOCOL.md commit **2de28513626ba1b456cb379fed5b082511e51653** BEFORE running any LIQMAP-005 economic outcome.
- Read-only Ironflow (ironflow.sh) public Hyperliquid original-position liquidation events and hourly candles, 2026-07-01..2026-10-31 inclusive, original file SHA256 validated against Hugging Face LFS. **BTC-PERP 248,855 + ETH-PERP 67,275 = 316,130 liquidated positions** and 2,952 consecutive complete hourly bars **per asset**, no market mixing. No wallet identifiers exposed.
- Both models use same **July 15..Aug 31 only** training data (1,152 hourly examples, 131 high-risk positives in each asset), with September (720 hourly points/asset) and October (740/asset) genuinely held out from **model fitting**. *Human research hypothesis was proposed after historical market observations*: not truly prospective/hypothesis-independent OOS. No tuning, model selection or fee changes after examining those test months.
- Risk label from actual high/low price excursion after the first next-hour OPEN over four following full hourly bars, compared to **nearest-rank 90th percentile of 333 complete earlier 4-hour excursions** all known by signal-close t. Future bars not used in features/reference thresholds. Price-only model features: trailing 4h absolute log-return, rolling 24h 1h log-return std, current closed candle log high/low. Additional liquidation features: log1p(current liquidated USD/(prior 336h 95th percentile USD+1)) and log1p(current actual liquidated positions).
- StandardScaler + fixed L2 logistic C=1 trained only in July/Aug, no calibration using September/October. Primary October Brier difference BRIER(price)-BRIER(price+liquidations); higher is better. Weekly block 2000 resamples seed 5005, 95% CI; Brier 0.005 threshold frozen, September confirmation also required. Do not pool BTC/ETH as independent samples.

## 2. Verified proof of execution
- PR Draft #403: https://github.com/joseluisvieira28-oss/Laboratorio/pull/403
- Actual successful GitHub Actions: **#45797830799** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45797830799
- Artifact original 15106335723 https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45797830799/artifacts/15106335723
- ZIP SHA256 **a50efb5f51dd406ce894e3bb7d7010581ea3415c92c5ba46b612bf6a7ba24b6d**. Source inventory / original LFS receipts, Brier/log-loss/AUC, ISO block confidence intervals, monthly portfolio utility and full gate results in artifact.
- **6/6 tests PASS**, including strict future-blind risk threshold, locked train/validation/test dates, next-hour source causality, no-guessed outcome, trading fee transitions and refusal to declare GO without all gates. An initial earlier CI run failed *only* due to a missing drawdown field in a synthetic test fixture; fixture was repaired, no strategy threshold or model changed. Subsequent #45797830799 entirely green.

## 3. PRIMARY risk-prediction results (Brier; LOWER is better)
| Month / Market | Samples | Risk events | Price-only Brier | Price+liquidations Brier | Improvement (positive=favorable) | Bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|---|
| September BTC | 720 | 72 | 0.089015 | 0.089057 | **−0.000042** | [−0.000735,+0.000421] |
| October BTC | 740 | 77 | 0.089664 | 0.090776 | **−0.001111** | **[−0.002040,−0.000065]** |
| September ETH | 720 | 68 | 0.087084 | 0.087461 | **−0.000377** | [−0.001109,+0.000076] |
| October ETH | 740 | 75 | 0.093284 | 0.093149 | **+0.000135** | [−0.000532,+0.000900] |

**Meaning:** On the primary holdout, the liquidation feature **worsens BTC calibration** even though October AUC slightly increased from 0.6345 to 0.6383. ETH's tiny improvement is statistically uncertain and 37x smaller than the preregistered +0.005 gate. September deteriorates for BOTH assets. Only ~5 ISO weekly blocks in October, overlapping hourly four-hour outcomes => wide/dependent uncertainty, bootstrap is exploratory.

Secondary October diagnostics:
- BTC log-loss price 0.318943 vs +liquidation 0.321917 (worse); AUC 0.63448 vs 0.63826 (small rise, does not override Brier).
- ETH log-loss price 0.334797 vs +liquidation 0.333775 (small rise in quality); AUC 0.53584 vs 0.54723 (still modest).

## 4. Business utility under a simple, *non-executable* LONG/CASH rule
- Non-overlapping UTC 4h decisions: p(high-risk) <=0.20 => hypothetical 1x LONG coin perp, else CASH; never short, no leverage. Same cutoff for both methods, passive 100% LONG comparator. Enter next hour OPEN, exit close t+4 for 4h gross interval; model fee 10bps per exposure change plus 5bps slippage per exposure change, flatten hypothetical at month-end. Funding, real liquidity, actual account fees, bid/ask spread and trader liquidation risk not included.
- Fixed lower stress: 10bps fees+5bps slippage PER SIDE, net MONTHLY simulations:

| Market / Month | Passive LONG | Price-only risk gate | Price + LIQ risk gate | Incremental EXT vs PRICE |
|---|---:|---:|---:|---:|
| BTC Sep | +5.82% | +6.74% | **+1.12%** | **−5.63pp** |
| BTC Oct | −7.48% | −5.84% | **−5.18%** | +0.65pp |
| ETH Sep | +8.29% | +6.43% | **+9.23%** | +2.80pp |
| ETH Oct | −16.44% | −16.68% | **−18.79%** | **−2.10pp** |

Only BTC October has a small positive improvement vs price-only and passive, and ETH October becomes worse. BTC October ext NAV 0.94817 vs price-only 0.94164 vs passive 0.92517; but BTC September price-only NAV 1.06744 vs ext 1.01116. ETH October ext NAV 0.81214 vs price-only 0.83316 vs passive 0.83556, and drawdown worsens to −21.13% vs price-only −19.09%.

- 35bps fees/side+5bps slip sensitivity: BTC Oct price-only −7.70% vs ext −7.52%; ETH Oct price-only −18.34% vs ext −20.79%. No consistent practical benefit.

## 5. Gate and verdict
The six+ fixed checks require in BOTH BTC and ETH: Oct sample >=500/positives >=40 (PASS), Oct Brier improvement >=.005 (FAIL BOTH), Oct weekly CI lower bound >0 (FAIL BOTH), September Brier improvement >0 (FAIL BOTH), Oct net LONG/CASH NAV ext beats price-only AND passive (PASS BTC ONLY), Oct drawdown no worse than price-only (PASS BTC ONLY), and ext beats price-only in BOTH September and October (FAIL BOTH).
- **Technical and source = GO for trustworthy historical evaluation.**
- **Scientific hypothesis "liquidations add predictive value" = NO-GO** for this frozen combination/timeframe and these months. Do not optimize same period until victory.
- **Business utility / live capital = NO-GO**, no edge demonstrated vs price-only after modeled costs and drawdown.
- These results DO NOT show whether funding/realized liquidations *generally* predict all future volatility horizons, do not test Neuron, and cannot prove absolute absence of all edges.

## 6. Next action
**Stop optimizing LIQMAP005 on this data.** Continue the already separately scheduled LIQMAP002 *point-in-time map* monitoring; do not modify that study. If there is genuine demand for a risk service, the next useful test would be independently validating one genuinely future, pre-registered alert model on days not yet observed, with exchange-fee/latency verification and clear decision utility; do NOT start a new task/bot merely to chase another PASS.
**No trades, money, accounts, orders, subscriptions, APIs with keys, buy/sell action, merge or deployment. PR remains Draft.**
