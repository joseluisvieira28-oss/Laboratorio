# CMM-PR-001 — CROSS-MARKET PRICE RESIDUAL
## DEVELOPMENT AUTHORITY V0.1 — 2026-09-25

STATUS: DEVELOPMENT / HYPOTHESIS-GENERATION ONLY
PRIMARY FAMILY: RV
SECONDARY FAMILY: MACRO
PROMOTION CREDIT: ZERO
2026: LOCKED / MUST NOT BE ACCESSED

## 1. WHY THIS SUCCESSOR EXISTS
CMM-MECH-001 demonstrated that the retired CMM-001 spot state,
S_raw(d)=ln(P[d]/P[d-7]),
can converge mechanically when the old return segment rolls out of the seven-day window.

CMM-PR-001 therefore does NOT use trailing-seven-day BTC state as "mispricing".

It asks a materially different question:

> Is the actual, directly observed 24-hour BTC price move unusually strong or weak relative to contemporaneous options/rates/stablecoin information, and does that causal residual subsequently mean-revert?

## 2. DEVELOPMENT CORPUS
2021-2025 is development-only and already contaminated by prior Crypto Lab research.
It may be used to build and falsify this exact mechanism but can earn ZERO Tier promotion credit.

Inputs are restricted to:
- CMM001_DAILY_STATE_LEDGER_V01.csv through 2024
  - Git blob SHA: c30a38638dcbd8dd33a5a627ad15a3a7096011ca
- CMM_DRV_001_2025_STATE_LEDGER_V01.csv
  - Git blob SHA: ee4c98340a29ef6c925ba07a543b7cce2e70920c
- official Binance Data Vision BTCUSDT Spot 1h archives needed for exact 17:00 and 18:00 UTC OPEN observations through 2025-12-31, every provider CHECKSUM verified.

No parent event/PnL ledger may be read.
No 2026 source or market data may be fetched.

## 3. NON-SPOT INFORMATION VECTOR
Use only already point-in-time normalized states:
X_t = [O_z(t), R_z(t), L_z(t)]

All three are required.
No median substitution.
No funding, CFTC, OI or additional feature may be added after this freeze.

## 4. DIRECT BTC PRICE VARIABLE
Contemporaneous actual BTC move:
Y_t = ln(P17[t] / P17[t-1])

This is a direct one-calendar-day price return.
It contains no 7-day rolling-return subtraction and therefore cannot normalize merely because a t-7 observation rolls out.

## 5. CAUSAL WALK-FORWARD FAIR-VALUE MODEL
For every eligible day t:

1. take exactly the prior 365 VALID complete observations, current day excluded;
2. estimate ordinary least squares:
   Y = a + bO*O_z + bR*R_z + bL*L_z
3. no regularization;
4. no feature selection;
5. no coefficient clipping;
6. predict Yhat_t from X_t;
7. raw residual E_t = Y_t - Yhat_t.

If the 4x4 normal-equation system is singular or non-finite, the day is invalid; no fallback model.

## 6. CAUSAL RESIDUAL NORMALIZATION
For every valid raw residual E_t:
- require exactly the prior 180 valid walk-forward residuals;
- current residual excluded;
- location = prior-180 median;
- scale = 1.4826 * prior-180 MAD;
- ZRES_t = (E_t - median) / scale;
- clip only for reporting at [-8,+8]; the unclipped value is used for the primary slope.

No threshold is used for the primary mechanism.

## 7. FROZEN FUTURE TARGET
Signal/state decision is considered available at 17:05 UTC.

Future target:
FWD24_t = ln(P18[t+1] / P18[t]) * 10,000 bps

This begins from the exact Binance Spot 18:00 UTC OPEN, after the state decision, and ends at the next calendar-day 18:00 UTC OPEN.

Mean-reversion orientation:
MR_GROSS_t = -sign(ZRES_t) * FWD24_t

No stop, target, leverage or asset substitution.

## 8. PRIMARY DEVELOPMENT TEST
Primary continuous regression:
FWD24_bps = alpha + beta * ZRES_unclipped + error

Expected mechanism sign:
beta < 0.

Also report:
- Spearman rho(ZRES, FWD24)
- mean/median MR_GROSS
- positive MR_GROSS fraction
- mean MR_NET10 = MR_GROSS - 10 bps, diagnostic only
- annual beta and mean MR_GROSS for each represented full year
- ZRES distribution.

## 9. INFERENCE
Use 5,000 moving-block bootstrap resamples of the ordered valid daily pairs:
- block length = 7 observations;
- seed = 20260925;
- statistic = beta;
- report p05, median, p95;
- no alternative block length after outcomes.

## 10. PRE-FROZEN DEVELOPMENT SURVIVAL GATE
This exact mechanism is worth a genuinely prospective forward test only if ALL:

1. N >= 500 valid ZRES/FWD24 observations.
2. overall beta < 0.
3. bootstrap beta p95 < 0.
4. Spearman rho < 0.
5. mean MR_GROSS > 0.
6. at least 2 calendar years with >=100 observations each have beta < 0.

If ALL pass:
DEV_MECHANISM_SURVIVES__FORWARD_ONLY_REQUIRED.

If any fails:
DEV_MECHANISM_FAIL__CLOSE_EXACT_RESIDUAL.

This is NOT a Tier verdict either way.

## 11. NO RESCUE
After first output:
- no alternate 180/365 window;
- no feature removal/addition;
- no ridge/lasso/Huber replacement;
- no residual threshold rescue;
- no long-only/short-only rescue;
- no alternate 17:00/18:00 clock;
- no 48h/72h target rescue;
- no favorable year/month subset;
- no 2026 historical rescue.

A failed mechanism closes CMM-PR-001-V0.1.

## 12. SAFETY / GOVERNANCE
Research only.
No live trading.
No micro-live.
No orders.
No exchange mutation.
No wallet.
No alerts/webhooks.
No Render deployment.
No merge to main.
No 2026 access.

END OF DEVELOPMENT AUTHORITY V0.1
