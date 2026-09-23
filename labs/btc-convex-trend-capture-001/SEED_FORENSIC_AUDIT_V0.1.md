# BTC-CONVEX-TREND-CAPTURE-001 — SEED FORENSIC AUDIT V0.1

**Date:** 2026-09-23  
**Evidence:** three user-supplied TradingView trade-list CSV exports  
**Scientific role:** retrospective seed characterization only

## 1. Closed-trade summary

| TF | Closed trades | Closed PnL | Win rate | PnL PF | Max DD | Max losing streak |
|---|---:|---:|---:|---:|---:|---:|
| 5m | 187 | +10,615.57 USDT | 20.32% | 1.083 | -68.99% | 16 |
| 15m | 159 | +3,251.69 USDT | 18.24% | 1.037 | -77.70% | 14 |
| 4h | 61 | +1,417.20 USDT | 27.87% | 1.075 | -39.51% | 10 |

The low PnL profit factors and very deep drawdowns do not support promotion.

## 2. Mechanism reconstruction from fills

### Position sizing

Mean position value / pre-trade equity:
- 5m: 94.905%
- 15m: 94.906%
- 4h: 94.905%

The seed backtest therefore puts almost the whole account into each trade.

### Hard stop

For normal stopped losers, exit price is almost exactly 4.000% below entry:
- 5m median: 4.000107%
- 15m median: 4.000105%
- 4h median: 4.000067%

This is strong evidence for an exact **4% hard price stop**.

### Trailing exit

For normal winners, exit price is approximately 12% below the observed favorable peak:
- 5m median inferred peak giveback: 11.913%
- 15m: 11.913%
- 4h: 11.913%

Many identical exit prices also recur across timeframes around the same market episodes, consistent with a common peak-trailing mechanism.

Strong seed inference:

**hard stop ~= 4% + trailing stop ~= 12% after an unknown activation condition.**

The activation rule itself is NOT proven by the trade list.

## 3. Tail dependence

All three systems are net negative after removing only the single best historical winner:

| TF | Best closed winner | Net PnL without best winner |
|---|---:|---:|
| 5m | +17,893.71 | -7,278.14 |
| 15m | +10,222.22 | -6,970.53 |
| 4h | +3,915.57 | -2,498.37 |

This is compatible with convex trend-following, but it means the result is highly dependent on rare right-tail events.

Gross-profit concentration is material:
- 5m top winner = 12.9% of all gross profit.
- 15m top winner = 11.2%.
- 4h top winner = 19.2%.

## 4. MFE leakage in eventual losers

Eventual losers that first reached positive MFE:

| Threshold | 5m | 15m | 4h |
|---|---:|---:|---:|
| MFE >= +4% | 60 / 149 | 55 / 130 | 21 / 44 |
| MFE >= +10% | 25 / 149 | 18 / 130 | 6 / 44 |
| MFE >= +15% | 3 / 149 | 2 / 130 | 0 / 44 |

This is enough to motivate an exit/profit-protection hypothesis. It is NOT enough to choose a threshold from this history and call the result independent.

## 5. Recent regime deterioration

Mean trade return, 2019-2024 vs 2025-2026 closed trades:

- 5m: +1.741% -> -1.994%
- 15m: +1.456% -> -2.171%
- 4h: +0.755% -> approximately flat

The currently open 2026 trade is a large winner in every export and materially improves the headline report. Open PnL is not treated as a closed scientific outcome here.

## 6. Cross-timeframe independence

Monthly closed PnL correlation:
- 5m vs 15m: ~0.87
- 5m vs 4h: ~0.18
- 15m vs 4h: ~0.17

Therefore 5m and 15m are economically close variants, not independent replications.

## 7. Risk-normalized descriptive counterfactual

Using the same realized trade-return sequence and only reducing capital allocation, approximate closed-period results are:

### 5m
- ~0.5% account risk per 4.19% stopped trade: +25.8%, max DD ~-13.2%
- ~1.0% risk: +50.9%, max DD ~-24.8%
- original ~4% account risk: +106.9%, max DD ~-68.9%

### 15m
- ~0.5% risk: +16.7%, max DD ~-16.0%
- ~1.0% risk: +30.8%, max DD ~-29.7%
- original ~4% risk: +32.9%, max DD ~-77.6%

### 4h
- ~0.5% risk: +4.5%, max DD ~-5.8%
- ~1.0% risk: +8.2%, max DD ~-11.3%
- original ~4% risk: +14.3%, max DD ~-39.5%

These are **risk-engineering counterfactuals**, not new backtest evidence and not proof of edge.

## 8. Statistical fragility

Non-parametric bootstrap of mean trade return produces 95% intervals that cross zero for all three timeframes, including block-bootstrap variants preserving local clustering.

That is consistent with a weak/uncertain expectancy dominated by rare large winners, not with a robustly demonstrated edge.

## Verdict

**OPEN LAB / MECHANISM WORTH INVESTIGATING / EDGE NOT ESTABLISHED.**

The most valuable next move is not parameter optimization. It is exact source recovery and causal reconstruction of the entry and trailing-activation logic.
