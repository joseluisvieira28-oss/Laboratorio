# DCV-001 — DERIVATIVES CROWDING × VOLATILITY INTERACTION — PRE-OUTCOME AUTHORITY V0.1

Date: 2026-09-23
Branch: `dcv001-funding-oi-vol-interaction-v0.1`
Repository: `joseluisvieira28-oss/Laboratorio`

## STATUS

FROZEN_PRE_SOURCE / RESEARCH_ONLY / OUTCOME_BLIND.

This is a NEW prospective hypothesis inspired by the historical ARQ-016 / LL-0014 idea ("funding/OI/volatility regime conditioning"). The archaeology audit established that LL-0014 itself was underspecified and NOT TESTED: no recoverable trigger, threshold, direction, horizon, cost model or executable protocol existed. Therefore DCV-001 does NOT claim to reconstruct LL-0014 and does not inherit any missing parameters from it.

## ANTI-DUPLICATION

DCV-001 is materially different from LL-0016-C. LL-0016-C tested a thresholded funding-extreme + open-interest-expansion crowd-unwind rule and closed NO_EDGE. DCV-001 does not reuse its thresholds, event definition, trade mapping, direction rule or costs.

DCV-001 asks an incremental-information question:

> Does realized-volatility state amplify the predictive interaction between BTC perpetual funding and open-interest change for next-day BTC mark-price returns?

No trading PnL is part of this lab. A positive mechanism result would require a separately frozen execution hypothesis later.

## PRIMARY ASSET

Exactly one instrument: Binance USD-M BTCUSDT perpetual / BTCUSDT mark-price series.

No cross-asset search. No asset substitution after outcomes.

## SOURCE AUTHORITY

Official public Binance sources only; zero credentials and zero cash cost.

1. Binance Vision USD-M daily metrics:
   `data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-YYYY-MM-DD.zip`
2. Binance Vision USD-M monthly fundingRate:
   `data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-YYYY-MM.zip`
3. Binance Vision USD-M monthly markPriceKlines, 1h:
   `data/futures/um/monthly/markPriceKlines/BTCUSDT/1h/BTCUSDT-1h-YYYY-MM.zip`
4. Published `.CHECKSUM` sidecars for every object acquired.

No REST fallback may silently replace a failed archive route. A different source route requires a new source authority before outcomes.

## TEMPORAL FIREWALL

Source warm-up / Discovery acquisition may touch:
- 2021-01-01 through 2023-12-31 for Discovery.
- Source-only 2024 probe objects are allowed for replication feasibility, but 2024 economic values/outcomes remain LOCKED until the Discovery gates pass.

Protected:
- 2025: LOCKED / FORBIDDEN.
- 2026: LOCKED / FORBIDDEN.

No live trading, orders, exchange mutation, wallet access, alerts/webhooks, deployment, or merge to main.

## SOURCE GATE V0.1

The source gate must inspect only archive integrity, file/schema structure and timestamps. It MUST NOT report or retain funding-rate values, OI values, price values, returns, PnL, strategy statistics or directional outcomes.

Fixed probes:
- 2021-06-15 / 2021-06
- 2022-06-15 / 2022-06
- 2023-06-15 / 2023-06
- 2024-06-15 / 2024-06

For each year the gate must verify:
- metrics ZIP + CHECKSUM;
- fundingRate ZIP + CHECKSUM;
- markPriceKlines 1h ZIP + CHECKSUM;
- ZIP readability;
- expected schema family;
- all parsed timestamps remain strictly before 2025-01-01;
- no duplicate timestamp identities inside the probe object;
- metrics file is non-empty and contains:
  `create_time,symbol,sum_open_interest,sum_open_interest_value,count_toptrader_long_short_ratio,sum_toptrader_long_short_ratio,count_long_short_ratio,sum_taker_long_short_vol_ratio`;
- funding file is non-empty and exposes timestamp + funding-rate columns compatible with the official archive schema;
- 1h mark-price file is non-empty, has standard kline structure and >=99% of expected hourly timestamps for the probe month.

Any checksum mismatch, protected-period timestamp, archive corruption, missing mandatory schema, or missing fixed probe is FAIL_CLOSED.

SOURCE_DATA_PASS releases only the full 2021-2023 source census. It does not release outcomes.

## FULL SOURCE CENSUS — BEFORE OUTCOMES

If V0.1 passes, acquire the exact 2021-01-01 through 2023-12-31 source corpus plus the minimum deterministic warm-up required by the frozen transformation.

Before any next-day return is computed, emit a census containing only:
- requested vs present daily metrics files;
- missing dates;
- duplicate/conflicting timestamps;
- monthly funding file coverage and timestamp continuity;
- hourly mark-price coverage and gaps;
- SHA256/checksum verification state;
- first/last timestamps;
- row counts.

Full-source minimums:
- metrics: >=99% of requested UTC calendar days present;
- funding: no missing monthly object and no timestamp gap >12 hours after the first valid observation;
- mark price 1h: >=99.5% expected hourly timestamps overall, no unresolved duplicate open_time, no gap >3 consecutive hours;
- zero protected 2025/2026 rows.

Failure => SOURCE_DATA_INSUFFICIENT or SOURCE_PROVENANCE_FAIL. No outcomes opened.

## FROZEN DAILY FEATURE CONSTRUCTION

Information day = UTC calendar day D.

All features for D use only information whose source timestamp is <= 23:59:59.999 UTC on D. Prediction target is the next completed UTC day, D+1.

### Open interest
For each UTC day D:
- sort valid metrics rows by create_time;
- take the chronologically last valid BTCUSDT row;
- `OI_D = sum_open_interest`;
- `oi_change_D = ln(OI_D / OI_{D-1})`.

No intraday threshold or alternative OI transform may replace this after outcomes.

### Funding
`funding_D` = arithmetic sum of all official BTCUSDT `last_funding_rate` observations whose funding timestamp falls inside UTC day D.

### Volatility
From official 1h mark-price closes:
- form hourly log returns;
- `rv7_D = sqrt(sum(r_h^2))` over the trailing 7 completed UTC days ending on D.

No annualization is needed because the variable is standardized below.

### Causal standardization
For each raw feature X in {funding_D, oi_change_D, rv7_D}:
- compute mean and sample standard deviation using the previous 90 valid information days D-90 ... D-1 only;
- `z_X(D) = (X_D - mean_past90) / sd_past90`;
- if sd=0 or any required source value is missing, D is not model-eligible;
- clip z to [-5,+5] prospectively.

The current day never contributes to its own normalization window.

## FROZEN OUTCOME

`r_next_D = ln(mark_close_{D+1} / mark_close_D)`

where `mark_close_D` is the final valid 1h BTCUSDT mark-price close whose open_time belongs to UTC day D.

This is a mechanism study, not an executable fill assumption.

## PRIMARY MODEL

For every eligible information day D:

`r_next_D = b0 + bF*F + bO*O + bV*V + bFO*(F*O) + bFV*(F*V) + bOV*(O*V) + bFOV*(F*O*V) + e`

where:
- F = funding z-score;
- O = OI-change z-score;
- V = realized-volatility z-score.

Primary parameter: `bFOV`.

Mechanistic directional hypothesis frozen before outcomes:
- `bFOV < 0`.

Interpretation: as volatility rises, increasingly positive funding combined with increasing OI is expected to be associated with weaker next-day returns, while the symmetric crowded-short state is expected to tilt the other way.

The lower-order terms are mandatory; the triple interaction may not be tested in isolation.

## DISCOVERY WINDOW

Economic outcomes opened only for model-eligible D whose D+1 lies in:
- 2021-01-01 through 2023-12-31.

The 90-day causal warm-up naturally delays the first eligible model date. No minimum-date adjustment may be chosen after seeing outcomes.

## PRIMARY INFERENCE

Moving-block bootstrap on chronological eligible daily rows:
- repetitions: 5,000;
- fixed RNG seed: 140017;
- block length: 7 observations;
- statistic: OLS estimate of `bFOV`;
- two-sided 95% percentile CI.

OLS must solve the full frozen 8-column design matrix. Singular bootstrap samples are discarded and counted; fewer than 4,750 valid bootstrap estimates => INFERENCE_TECHNICAL_FAIL.

## DISCOVERY GATES — ALL REQUIRED

1. Source census PASS.
2. Eligible Discovery N >= 900.
3. Full-design rank = 8.
4. `bFOV < 0`.
5. 95% bootstrap upper bound for `bFOV < 0`.
6. Calendar-year full-model `bFOV` sign is negative in at least 2 of 3 years: 2021, 2022, 2023.
7. No source/provenance/firewall violation.

If any gate fails: DISCOVERY_FAIL_NO_PROMOTION. Exact DCV-001 model closes; no sign inversion, thresholding, alternate z-window, feature substitution, asset substitution, horizon change or favorable-year selection.

If all pass: DISCOVERY_MECHANISM_PASS and only then release the pre-frozen 2024 replication.

## PRE-FROZEN 2024 REPLICATION

Same source family, feature transformations, 90-day causal normalization, model formula, expected sign and inference code.

2024 gates:
1. eligible N >=300;
2. `bFOV <0`;
3. 90% moving-block-bootstrap upper bound <0, same block length 7 and seed 140017;
4. source/provenance integrity PASS.

All required => MECHANISM_REPLICATION_PASS_CANDIDATE.
Any failure => REPLICATION_FAIL_NO_PROMOTION.

Even a replication PASS is NOT a tradable edge, does NOT authorize PnL construction, and does NOT open 2025 or 2026.

## FORBIDDEN RESCUES

After any economic outcome is opened, do not:
- invert the coefficient sign;
- add/remove predictors;
- change 90-day normalization;
- change 7-day volatility window;
- change next-day horizon;
- switch mark price to spot/index/trade price;
- choose thresholds or quantiles;
- change block length/seed to improve inference;
- subset favorable years;
- add ETH/altcoins;
- import LL-0016 thresholds;
- open 2024 if Discovery fails;
- open 2025/2026 under this authority.

## CLASSIFICATION BOUNDARY

A source failure is not NO_EDGE.
A statistical Discovery failure is not a source failure.
A mechanism PASS is not SCIENTIFIC TRADING EDGE and not live-trading authority.
