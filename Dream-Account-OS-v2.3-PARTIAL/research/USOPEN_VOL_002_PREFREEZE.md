# USOPEN-VOL-002 — U.S. CASH OPEN VOLATILITY SHOCK — POST-ETF 2024 REPLICATION — PRE-FREEZE

Date frozen: 2026-09-23
Parent: `USOPEN-VOL-001 / USOV-PREETF-001`
MVE: `USOV-POSTETF-2024-001`
Status: PRE_REPLICATION_FROZEN
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Production impact: NONE
Live execution: FALSE

## Scientific question

After U.S. spot Bitcoin ETPs began trading, does the exact pre-ETF 09:30 America/New_York crypto realized-variance concentration replicate in the 2024 post-launch regime without changing the clock, windows, estimator, universe or threshold logic?

A secondary, pre-specified structural comparison asks whether the OPEN/PRE effect is amplified, attenuated, or statistically indistinguishable from the frozen 2022–2023 Discovery regime.

This remains a **non-directional mechanism replication**. It computes no trading PnL.

## External regime boundary

The SEC approved listing and trading of spot Bitcoin ETP shares on 2024-01-10. The products commenced public trading on 2024-01-11. Therefore the frozen post-ETF sample begins on **2024-01-11**, not January 1.

NYSE authority defines the Core Open Auction and Core Trading Session start at **09:30 ET**.

The post-ETF label is a regime boundary, not a claim of ETF causality. Any detected change may reflect contemporaneous market-structure changes.

## Exact inherited clock and estimator

For each regular U.S. cash-market trading day:
- PRE: 09:00–09:30 ET
- OPEN: 09:30–10:00 ET
- POST: 10:00–10:30 ET

Each window contains exactly six completed 5-minute bars.

Realized variance:
`sum(log(close_t / close_{t-1})^2)`

Primary contrasts:
- OPEN / PRE
- OPEN / POST

Universe inherited unchanged:
BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT on Binance USD-M Futures public 5m archive.

## Frozen replication gate

Post-ETF 2024 exact replication survives only if all are true:
- at least 1,350 eligible symbol-days;
- pooled median OPEN/PRE >= 1.20;
- date-cluster bootstrap 95% lower bound OPEN/PRE > 1.05;
- pooled median OPEN/POST >= 1.10;
- date-cluster bootstrap 95% lower bound OPEN/POST > 1.00;
- at least 4 of 6 symbols have median OPEN/PRE > 1.10.

No annual breadth gate is possible because this replication opens one calendar year only.

## Frozen structural comparison

The 2024 post-ETF OPEN/PRE log-ratio distribution is compared with the already-open 2022–2023 pre-ETF Discovery regime using an independent date-cluster bootstrap preserving all symbols within each sampled U.S. trading date.

Classification:
- AMPLIFIED if the 95% CI lower bound of exp(median_log_ratio_2024 - median_log_ratio_2022_23) is > 1;
- ATTENUATED if the 95% CI upper bound is < 1;
- NO_DETECTABLE_SHIFT otherwise.

This comparison does not establish ETF causality.

## Firewall

Allowed:
- public/free Binance acquisition;
- recomputation of already-open 2022–2023 baseline solely for the pre-frozen structural comparison;
- opening **2024-01-11 through 2024-12-31 only**;
- immutable receipt and closeout.

Forbidden:
- opening 2025 or 2026;
- using 2024-01-01 through 2024-01-10 in the post-ETF sample;
- directional returns or PnL;
- window/clock/asset tuning;
- weekday/month selection;
- macro-day exclusion after outcomes;
- BTC-only rescue;
- threshold changes after outcomes;
- variance-estimator substitution;
- live trading;
- exchange mutation;
- merge to main.
