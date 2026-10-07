# MEXC-MULTI-STABLE-BASIS-001 — PROSPECTIVE PRE-OUTCOME FREEZE V0.3

Date: 2026-10-07
Status: FROZEN BEFORE CALIBRATION PREDICTOR VALUES AND BEFORE ANY ECONOMIC OUTCOME

## 1. Parent scientific state

- Current public source gate: `SOURCE_PASS`.
- Historical economic path: `HISTORICAL_SOURCE_BLOCKED_INSUFFICIENT_COMMON_COVERAGE`.
- No historical Development/OOS economic outcome has been opened.
- V0.3 is strictly prospective and does not rescue the historical path.

## 2. Mechanism

Same-underlying MEXC perpetuals margined/settled in different stablecoins can temporarily diverge after normalization because margin inventory, settlement-coin demand, venue segmentation and local order-flow pressure differ across USDT, USDC and USD1 books.

Frozen hypothesis:
A sufficiently extreme cross-stablecoin normalized price range mean-reverts over a short horizon.

Direction is fixed BEFORE outcomes:
- SHORT the richest normalized perpetual;
- LONG the cheapest normalized perpetual.

No directional BTC/ETH market view is intended.

## 3. Frozen universe

Underlyings:
- BTC
- ETH

Perpetual triplets:
- BTC_USDT / BTC_USDC / BTC_USD1
- ETH_USDT / ETH_USDC / ETH_USD1

Stablecoin normalization:
- USDT leg multiplier = 1
- USDC leg multiplier = exact MEXC Spot USDCUSDT closed 1m close
- USD1 leg multiplier = exact MEXC Spot USD1USDT closed 1m close
- USD1USDC is diagnostic consistency only and cannot rescue missing required normalization.

No asset, settlement coin or external venue may be added after outcomes.

## 4. Predictor-only calibration — outcome seal remains closed

Calibration window is frozen as:
`2026-09-29T00:00:00Z <= t < 2026-10-07T00:00:00Z`

For every exact common closed minute t and each underlying:

`P_USDT_norm(t) = P_USDT_perp(t)`

`P_USDC_norm(t) = P_USDC_perp(t) * USDCUSDT_spot(t)`

`P_USD1_norm(t) = P_USD1_perp(t) * USD1USDT_spot(t)`

Use natural logarithms.

`range_bps(t) = 10000 * (max(log(P_norm_i(t))) - min(log(P_norm_i(t))))`

Calibration may read ONLY contemporaneous predictor inputs above.

Calibration MUST NOT calculate or inspect:
- any t+1 or later return conditional on the predictor;
- convergence;
- winner/loser outcome;
- trade PnL;
- execution outcome;
- any alternative horizon.

Per-underlying threshold:
nearest-rank q99 of `range_bps` over the frozen calibration window.

Calibration source gate:
- >=95% of the 11,520 expected minutes must have exact common timestamps for all three perpetual legs and both required normalization routes for that underlying;
- no forward fill, interpolation or nearest-neighbor repair.

If calibration source gate fails:
`PROSPECTIVE_SOURCE_BLOCKED_CALIBRATION`.

Once q99 thresholds are calculated they must be committed in an immutable threshold receipt BEFORE any prospective economic observation is admitted.

## 5. Prospective boundary

The economic forward boundary is:
the first complete UTC minute strictly AFTER the commit timestamp of the immutable calibration-threshold receipt.

No minute at or before that boundary may ever enter V0.3 economics.

No backfill.

## 6. Signal

At each fully closed 1m minute t after the prospective boundary:

For each underlying:
1. require exact same-minute closes for all three perpetuals + USDCUSDT + USD1USDT;
2. calculate normalized prices exactly as in calibration;
3. calculate frozen `range_bps(t)`;
4. signal if `range_bps(t) >= q99_threshold_underlying`;
5. rich leg = highest normalized price;
6. cheap leg = lowest normalized price;
7. direction = SHORT rich / LONG cheap.

Ties or ambiguous ordering are ineligible.

BTC and ETH signals at the same t form ONE equal-weight event basket.

Global event cooldown = 15 minutes, equal to the primary holding horizon. Later signals inside cooldown are recorded but not admitted.

## 7. Funding-window exclusion

This is a short-horizon convergence study, not a funding-capture study.

Any candidate whose entry-to-exit window would cross a scheduled funding settlement for EITHER selected perpetual leg is deterministically `FUNDING_WINDOW_INELIGIBLE` and excluded before outcome scoring.

No funding outcome may be used to include/exclude after the fact.

## 8. Executable shadow model

Primary notional:
- 25 USDT-equivalent per leg
- total gross pair exposure = 50 USDT-equivalent

Report-only capacity sensitivities:
- 10 / 50 / 100 USDT-equivalent per leg

Entry:
- first public MEXC depth snapshot for BOTH selected legs after signal close;
- both books captured within 30 seconds of t;
- quantize contracts using live public contractSize / volUnit / minVol;
- consume actual public book depth;
- both legs must be fully fillable;
- no maker assumption.

Exit:
- exactly t + 15 minutes;
- first public MEXC depth snapshot for BOTH legs within 30 seconds;
- close exactly the same contract quantities;
- both exits must be fully fillable.

Stablecoin valuation:
- use fresh public MEXC Spot USDCUSDT / USD1USDT best bid-ask mid for USDT-equivalent accounting;
- max age 5 seconds;
- valuation is accounting normalization, not an assumed spot conversion trade;
- report spot spread as a diagnostic.

## 9. Fees and friction

Primary API-taker fee:
- 8 bps per executed transaction per leg.
- Apply fee explicitly to every entry/exit fill.

For equal-weight pair return on gross pair exposure, this corresponds to 16 bps round-trip fee drag before book slippage.

Stress fee:
- 12 bps per executed transaction per leg
- equivalent 24 bps round-trip on gross pair exposure before book slippage.

Book slippage is measured from captured depth and is additional to fees.

No promotional, maker or account-specific fee rescue.

## 10. Event economics

For each admitted underlying trade:
- calculate signed PnL of long-cheap + short-rich using executable entry/exit fills;
- convert settlement-currency PnL to USDT-equivalent using frozen valuation rule;
- divide by total gross pair entry exposure;
- report gross bps, primary-net bps and stress-net bps.

If BTC and ETH share one admitted timestamp:
event-basket return = equal-weight mean of their complete underlying-trade returns.

Incomplete underlying execution makes that underlying ineligible.
If no complete underlying remains, the event basket is source/execution invalid.

## 11. Frozen minimum evidence gate

Do not adjudicate economics until ALL:
- >=40 admitted event baskets;
- >=7 distinct UTC dates;
- BTC has >=10 admitted underlying trades;
- ETH has >=10 admitted underlying trades;
- no single UTC date >35% of admitted event baskets;
- >=95% of pre-cooldown triggered underlying trades have complete timing-qualified executable entry+exit evidence;
- zero unresolved duplicate/evidence conflicts.

Before then:
`PROSPECTIVE_ACCUMULATING`.

## 12. Frozen survival gates — primary 25 USDT/leg

After minimum evidence is reached, run once.

PASS requires ALL:
1. mean primary-net event-basket bps > 0;
2. median primary-net event-basket bps > 0;
3. chronological first-half mean primary-net > 0;
4. chronological second-half mean primary-net > 0;
5. exact one-sided sign test on event-basket primary-net > 0 has p < 0.05;
6. leave-one-UTC-date-out mean primary-net > 0 for every date;
7. mean stress-net event-basket bps > 0;
8. execution/source completeness gate remains >=95%;
9. no evidence-chain or duplicate conflict.

If sample gate is met and any economic/statistical stability gate fails:
`NO_EDGE_PROSPECTIVE_AT_FROZEN_V03_GATE`.

If evidence quality prevents valid adjudication:
`BLOCKED_DATA_QUALITY` or `EXECUTION_SOURCE_BLOCKED`, not NO_EDGE.

If every gate passes:
`SURVIVES_PROSPECTIVE_MULTI_STABLE_BASIS_V03`.

## 13. Promotion ceiling

Even survival does NOT authorize live trading or micro-live.

A survivor requires a later separate execution/risk authority review.

## 14. No-rescue rules

After calibration predictor values or prospective outcomes are opened:
- do not change q99 to q95/q97/q99.5;
- do not change 15m horizon;
- do not test alternative directions to rescue;
- do not drop USDC or USD1 because one performs poorly;
- do not split BTC/ETH after seeing outcomes to promote only the winner;
- do not change cooldown;
- do not change primary notional or fee model;
- do not use the 27-day historical window as retrospective OOS;
- do not backfill missed forward minutes.

## 15. Governance

Research-only.
No main merge.
No live trading.
No orders.
No private/authenticated endpoints.
No account reads.
No balances/positions.
No wallets.
No exchange mutation.
No spending.
No post-outcome tuning.
