# OPTIONS-EXPIRY-REVERSAL-001 — FROZEN PRE-SOURCE PROTOCOL V0.1

STATUS: **FROZEN BEFORE ANY NEW BTC INTRADAY OUTCOME ACCESS**

LAB: `OPTIONS-EXPIRY-REVERSAL-001`  
MVE: `OER-BTC-EXPIRY-INTENSITY-30M-001`

## 1. Scientific question

Do BTC option expirations exert stronger short-horizon reversal pressure around Deribit's 08:00 UTC settlement when a larger fraction of pre-settlement BTC option trading is concentrated in contracts expiring at that settlement?

This is a new mechanism-specific experiment. It is not a rescue or retuning of `OPTIONS-SPOTPERP-001`, whose frozen trade-implied skew MVE remains closed as `DISCOVERY_FAIL_NO_PROMOTION`.

## 2. Mechanism

Deribit BTC options settle/expire at 08:00 UTC. The delivery-price window is formed immediately before settlement. Dealer hedging/position unwinds may create price pressure before expiry and reversal after the settlement discontinuity. Full historical OI/Greek/GEX history is not available under the required free/reproducible data posture, so **no historical GEX or dealer inventory is fabricated** in this MVE.

Instead, the MVE uses a point-in-time trade-derived **expiry activity intensity** as a minimal pressure proxy.

## 3. Immutable options source

Reuse only the already-preserved Deribit BTC option-trade raw corpus from the prior source audit:

- source branch: `options-spotperp-v0.1`;
- immutable monthly raw run: `34774293327`;
- immutable raw artifact: `options-spotperp-001-monthly-raw-34774293327-1`;
- raw artifact ZIP SHA256 observed in the canonical prior Discovery chain: `bcccd53db114221c948feaff5a8691f0710b7045e7dcac441c250c09eb443cda`;
- prior latest-code source-gate run: `34784590423`;
- prior source-gate artifact: `options-spotperp-001-final-latest-source-gate-34784590423-1`;
- protected raw period: 2021-04-01 00:00:00 UTC through 2024-12-31 23:59:59.999 UTC;
- 2025 and 2026 must remain inaccessible.

The new source gate may read only the Deribit option-trade `raw/` pages plus their immutable manifests/receipts. It must not read the old Binance price files bundled in the prior artifact.

## 4. Expiry-pressure source variable

For each UTC settlement date `d`, define the **pre-settlement source window**:

`[d-1 08:00:00 UTC, d 07:30:00 UTC)`

The final 30 minutes before 08:00 are deliberately excluded from the source variable so that the option-pressure classifier is complete before the later BTC pre-return window begins.

From public BTC inverse-option trades in that source window:

- `total_option_volume_btc(d)` = sum of public trade `amount` across all canonical BTC option instruments;
- `expiring_option_volume_btc(d)` = sum of `amount` only for instruments whose encoded expiry date is `d`;
- `expiry_activity_share(d)` = `expiring_option_volume_btc / total_option_volume_btc`, with zero only when total volume is zero.

No IV, skew, future return, PnL, BTC price outcome or OI/GEX is required for this source variable.

## 5. Past-only high-pressure classifier

A date becomes source-evaluable only after 30 complete prior settlement windows exist.

Frozen first possible signal date: `2021-05-02`.  
Frozen final signal date: `2024-12-31`.

For each evaluable date `d`:

- compute the median `expiry_activity_share` over the **previous 30 settlement dates only**;
- `HIGH_EXPIRY_PRESSURE(d) = 1` iff current share is strictly greater than that trailing past-only median;
- otherwise `HIGH_EXPIRY_PRESSURE(d) = 0`.

No percentile sweep, alternative lookback, z-score, smoothing, threshold tuning or post-outcome reclassification is authorized.

## 6. Source/data gate — before BTC outcomes

The source gate must establish, without reading BTC intraday outcomes:

1. prior raw manifest and latest-code source gate are valid and protected-period only;
2. every parsed trade timestamp lies before 2025-01-01;
3. canonical BTC option instrument parsing succeeds sufficiently to build the source series;
4. source windows are complete for the frozen signal period;
5. at least 800 evaluable source dates exist;
6. at least 150 HIGH_EXPIRY_PRESSURE dates exist;
7. HIGH_EXPIRY_PRESSURE has at least 15 observations in partial 2021 and at least 30 observations in each full year 2022, 2023 and 2024;
8. no BTC price, return, PnL, 2025 or 2026 data is accessed.

Failure is `DATA_FAILURE` or `INSUFFICIENT_SAMPLE` as appropriate, not `NO_EDGE`.

## 7. Frozen BTC outcome — only after SOURCE_DATASET_PASS

BTC outcome source: official Binance BTCUSDT Spot 1-minute archive, protected 2021-05-02 through 2024-12-31 only.

For each source-evaluable date `d`:

- `r_pre(d)` = BTC log/percentage return from 07:30:00 to 08:00:00 UTC;
- one-minute execution/finality buffer after settlement;
- `r_post(d)` = BTC return from 08:01:00 to 08:31:00 UTC.

2025 and 2026 remain locked.

## 8. Primary hypothesis and inference

Frozen primary model:

`r_post = alpha + beta_pre*r_pre + beta_high*HIGH + beta_int*(r_pre*HIGH) + weekday fixed effects + year fixed effects + error`

Primary one-sided hypothesis:

`H1: beta_int < 0`

Interpretation: reversal of the pre-settlement move is stronger when expiry activity pressure is high.

Frozen inference:

- 7-calendar-day moving-block bootstrap;
- 20,000 replications;
- seed `20260914`;
- one-sided alpha `0.05`;
- the primary interaction test cannot be rescued by companion economics.

No horizon sweep, clock-time sweep, lookback sweep, alternate threshold, nonlinear rescue, subperiod rescue or ML is authorized.

## 9. Companion executable economics

Only on HIGH_EXPIRY_PRESSURE dates:

- if `r_pre > 0`, short BTC at 08:01 UTC;
- if `r_pre < 0`, long BTC at 08:01 UTC;
- if `r_pre = 0`, no trade;
- exit at 08:31 UTC.

Report gross, NET10 and NET14 bps/trade, profit factor at NET14, cumulative return, max drawdown, win rate, and calendar-year partitions.

## 10. Promotion gates

Promotion requires **all** of the following:

1. source/provenance gate PASS;
2. `beta_int < 0`;
3. one-sided moving-block-bootstrap `p <= 0.05`;
4. mean NET10 > 0;
5. mean NET14 > 0;
6. profit factor NET14 > 1.00;
7. at least 3 of 4 calendar partitions (2021 partial, 2022, 2023, 2024) have non-negative NET14 mean;
8. no single calendar partition contributes more than 60% of total positive gross PnL.

If any gate fails, this exact MVE is not promoted. No post-outcome rescue is authorized.

## 11. Governance

- research-only;
- fail-closed;
- no live trading;
- no exchange mutation;
- no merge to main;
- no Render deployment;
- no 2025/2026 access;
- no GEX/OI reconstruction under incomplete historical data;
- no post-outcome tuning;
- failed hypotheses remain failed.
