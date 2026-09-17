# NFP-SURPRISE-V2 — 2025 MACRO SOURCE / SIGNAL FREEZE V0.1

Date: 2026-09-17
Status: **FROZEN_PRE_MARKET_OUTCOME**
Repository: `joseluisvieira28-oss/Laboratorio`
Branch: `nfp-surprise-v2-2025-oos-v01`
Parent protocol: `NFP-SURPRISE-V2-REPLICATION-01 — PRE-OUTCOME FREEZE — 2026-09-14`
Promotion governance: `ND-PROMOTION-POLICY-V3.0-FROZEN`

## Purpose

Resolve the historical `BLOCKED_BY_CONSENSUS_PROVENANCE_INCOMPLETE` state outcome-blind, before opening any protected 2025 BTCUSDT/ETHUSDT event return. This document freezes the complete calendar-2025 macro corpus, source precedence, consensus values, official first-release actuals and mechanically derived macro labels.

This is a macro/source freeze only. At the time of this commit:

- no BTCUSDT or ETHUSDT 2025 08:31→08:45 event return has been opened for NFP-SURPRISE-V2;
- no crypto PnL has been computed;
- no 2026 data are authorized or required;
- no live trading, orders, wallet access, exchange mutation, alerts, webhooks or merge to `main` are authorized.

## Immutable source precedence

Consensus fields are resolved independently and before market outcomes using this hierarchy:

1. contemporaneous pre-release Reuters/LSEG/Refinitiv poll or market-consensus reporting;
2. if a required field is absent from tier 1, a timestamped pre-release institutional/market publication explicitly reporting consensus/expectations for that field;
3. if a required field remains missing, is only a single-house forecast, is post-release reconstructed, or a conflict cannot be resolved by the hierarchy, the event fails provenance and the entire 2025 market-outcome stage remains blocked.

A lower-tier source may fill only a missing field. It cannot override an available higher-tier consensus value. No source may be selected because it creates a preferred HOTTER/COOLER label or crypto result.

## Frozen macro formula

For each release:

- Payroll actual > consensus: `+1`; < consensus: `-1`; equality: `0`.
- Unemployment actual < consensus: `+1`; > consensus: `-1`; equality: `0`.
- AHE MoM actual > consensus: `+1`; < consensus: `-1`; equality: `0`.
- Sum > 0: `HOTTER`; sum < 0: `COOLER`; sum = 0: `NEUTRAL`.
- `NEUTRAL` is mechanically non-directional. It is not a post-outcome deletion.
- No magnitude weighting, threshold, learned weights, component selection or revision substitution.

Official actuals are BLS **first-release** values only.

## Frozen 2025 macro ledger

| Release date | Reference month | Payroll consensus (k) | U-rate consensus | AHE MoM consensus | Payroll actual (k) | U-rate actual | AHE MoM actual | Votes (P/U/AHE) | Label |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 2025-01-10 | Dec 2024 | 160 | 4.2% | 0.3% | 256 | 4.1% | 0.3% | +1/+1/0 | HOTTER |
| 2025-02-07 | Jan 2025 | 170 | 4.1% | 0.3% | 143 | 4.0% | 0.5% | -1/+1/+1 | HOTTER |
| 2025-03-07 | Feb 2025 | 160 | 4.0% | 0.3% | 151 | 4.1% | 0.3% | -1/-1/0 | COOLER |
| 2025-04-04 | Mar 2025 | 135 | 4.1% | 0.3% | 228 | 4.2% | 0.3% | +1/-1/0 | NEUTRAL |
| 2025-05-02 | Apr 2025 | 130 | 4.2% | 0.3% | 177 | 4.2% | 0.2% | +1/0/-1 | NEUTRAL |
| 2025-06-06 | May 2025 | 130 | 4.2% | 0.3% | 139 | 4.2% | 0.4% | +1/0/+1 | HOTTER |
| 2025-07-03 | Jun 2025 | 110 | 4.3% | 0.3% | 147 | 4.1% | 0.2% | +1/+1/-1 | HOTTER |
| 2025-08-01 | Jul 2025 | 110 | 4.2% | 0.3% | 73 | 4.2% | 0.3% | -1/0/0 | COOLER |
| 2025-09-05 | Aug 2025 | 75 | 4.3% | 0.3% | 22 | 4.3% | 0.3% | -1/0/0 | COOLER |
| 2025-11-20 | Sep 2025 | 50 | 4.3% | 0.3% | 119 | 4.4% | 0.2% | +1/-1/-1 | COOLER |
| 2025-12-16 | Nov 2025 | 50 | 4.4% | 0.3% | 64 | 4.6% | 0.1% | +1/-1/-1 | COOLER |

Frozen directional sample: **9 events**. Frozen neutral sample: **2 events** (`2025-04-04`, `2025-05-02`).

October 2025 Employment Situation was not published because of the 2025 lapse in federal appropriations. The delayed September report was released 2025-11-20; the November report was released 2025-12-16. The December-2025 reference-month report belongs to January 2026 and is excluded because the replication window is calendar-2025 releases and 2026 remains locked.

## Consensus provenance register

The following public pre-release authorities were recovered and inspected before crypto outcomes. Where Reuters/LSEG did not expose a required field in the accessible pre-release text, the missing field is filled by a timestamped pre-release market-consensus source under the frozen precedence rule.

- 2025-01-10: Reuters syndicated pre-release reporting / market expectation: payroll +160k, unemployment 4.2%, AHE MoM +0.3%.
  - https://www.bworldonline.com/world/2025/01/10/646226/slow-steady-us-job-growth-seen-in-december/
- 2025-02-07: LSEG/Refinitiv `The Day Ahead`: payroll +170k, unemployment 4.1%, AHE MoM +0.3%.
  - https://share.refinitiv.com/assets/newsletters/The_Day_Ahead/TDAGeneric_NAM_02072025.pdf
- 2025-03-07: contemporaneous pre-release consensus: payroll +160k, unemployment 4.0%, AHE MoM +0.3%.
  - Reuters market preview family plus timestamped same-morning consensus cross-check.
- 2025-04-04: timestamped pre-release market calendar: payroll +135k, unemployment 4.1%, AHE MoM +0.3%.
  - https://www.forexlive.com/news/what-are-the-main-events-for-today-20250404/
- 2025-05-02: Reuters pre-release: payroll +130k, unemployment 4.2%, AHE MoM +0.3%.
  - https://www.reuters.com/sustainability/sustainable-finance-reporting/tariff-induced-uncertainty-seen-curbing-us-job-growth-april-2025-05-02/
- 2025-06-06: Reuters pre-release: payroll +130k, unemployment 4.2%, AHE MoM +0.3%.
  - https://www.reuters.com/world/us/slow-us-job-growth-anticipated-may-unemployment-rate-seen-steady-2025-06-06/
- 2025-07-03: Reuters pre-release: payroll +110k, unemployment 4.3%; contemporaneous pre-release consensus cross-check supplies AHE MoM +0.3%.
  - https://www.reuters.com/business/global-markets-trading-day-graphic-2025-07-02/
- 2025-08-01: Reuters pre-release: payroll +110k, unemployment 4.2%; timestamped pre-release market source supplies AHE MoM +0.3%.
  - https://www.reuters.com/world/us/slow-us-job-gains-expected-july-unemployment-rate-forecast-rising-42-2025-08-01/
  - https://www.esperio.net/analytics/market-analysis/market-news/4054051
- 2025-09-05: Dow Jones/market-calendar contemporaneous pre-release consensus: payroll +75k, unemployment 4.3%, AHE MoM +0.3%.
  - contemporaneous Dow Jones calendar syndicated on 2025-09-05.
- 2025-11-20: timestamped 04:15 ET pre-release market consensus: payroll +50k, unemployment 4.3%, AHE MoM +0.3%.
  - https://www.investing.com/analysis/nfp-preview-why-delayed-september-data-could-still-tilt-the-feds-decision-200670396
- 2025-12-16: higher-tier Reuters pre-release unemployment consensus 4.4% is frozen where accessible; payroll consensus +50k and AHE MoM +0.3% are corroborated by timestamped pre-release market sources. A lower-tier source reports unemployment 4.5%; this discrepancy is explicitly retained rather than hidden. The macro label is `COOLER` under either 4.4% or 4.5%, so the discrepancy is label-invariant and is not used to choose the source.
  - https://www.investing.com/analysis/nfp-preview-why-the-delayed-jobs-report-could-lead-to-a-us-dollar-rally-200671852

No post-release page is used as primary consensus authority.

## Official BLS first-release authority

- 2025-01-10: https://www.bls.gov/news.release/archives/empsit_01102025.htm
- 2025-02-07: https://www.bls.gov/news.release/archives/empsit_02072025.htm
- 2025-03-07: https://www.bls.gov/news.release/archives/empsit_03072025.htm
- 2025-04-04: https://www.bls.gov/news.release/archives/empsit_04042025.htm
- 2025-05-02: https://www.bls.gov/news.release/archives/empsit_05022025.htm
- 2025-06-06: https://www.bls.gov/news.release/archives/empsit_06062025.htm
- 2025-07-03: https://www.bls.gov/news.release/archives/empsit_07032025.htm
- 2025-08-01: https://www.bls.gov/news.release/archives/empsit_08012025.htm
- 2025-09-05: https://www.bls.gov/news.release/archives/empsit_09052025.htm
- 2025-11-20: https://www.bls.gov/news.release/archives/empsit_11202025.htm
- 2025-12-16: https://www.bls.gov/news.release/archives/empsit_12162025.htm

## Frozen crypto-market rule — not yet executed at this freeze

Assets: `BTCUSDT` and `ETHUSDT`, Binance Spot, required as one family.

For each of the 9 directional releases:

- release authority: 08:30 `America/New_York`;
- entry: exact **08:31 open**;
- exit: exact **08:45 open**;
- HOTTER: short-aligned return = `-log(exit_open / entry_open)`;
- COOLER: long-aligned return = `+log(exit_open / entry_open)`;
- BASE round-trip cost: **10 bps** per asset/event;
- no alternate minute, horizon, cost, asset or direction after outcomes.

## Frozen terminal metrics / V3 adjudication

For each asset report N, gross mean/median, NET10 mean/median, positive-event fraction, PF NET10, cumulative net diagnostic and max drawdown diagnostic.

Family event NET10 is the equal-weight average of BTC and ETH NET10 for the same event.

Hard scientific gates inherited from the frozen replication authority:

1. provenance/timestamp/leakage integrity PASS;
2. no event deletion or asset selection;
3. BTC mean NET10 > 0;
4. ETH mean NET10 > 0;
5. BTC PF NET10 >= 1.00;
6. ETH PF NET10 >= 1.00;
7. at least 5 of 9 directional events have positive family-average NET10;
8. largest single-event share of total positive family gross PnL <= 50%;
9. 2026 not accessed.

Also report leave-one-event-out minimum family-average NET10. A negative LOO minimum is a fragility flag, not by itself an automatic kill-switch under the frozen authority.

Uncertainty must be visible. Freeze diagnostic bootstrap now: **10,000 event-level bootstrap resamples, seed 20260917**, of the 9 family-average NET10 event values; report the 2.5%, 50% and 97.5% percentiles. It is diagnostic and cannot override failed base-economic hard gates.

Classification map:

- source/provenance/execution blocker before valid outcomes => `BLOCKED` / `PROVENANCE_FAILURE` / `TECHNICAL_FAILURE`, outside Tier 4;
- valid outcomes with materially failed independent family base economics => `TIER4_REJECTED` for this exact replication path;
- positive but mixed/fragile result that does not satisfy all hard gates => `TIER3_POSITIVE_OR_MIXED`;
- all hard gates PASS => `TIER2_PROMOTED_CANDIDATE__QUASE_DIAMANTE` under V3, not Tier 1 and not live-capital authorization.

## Governance firewall

This freeze cannot be amended after crypto outcomes to change consensus values, event inclusion, votes, labels, assets, direction, entry/exit, costs, bootstrap seed, gates or classification thresholds.

Any purely technical correction after execution starts must be demonstrated to occur before valid scientific output, documented independently and leave every scientific invariant unchanged.

**2026 LOCKED. NO LIVE TRADING. NO ORDERS. NO EXCHANGE MUTATION. NO WALLET. NO ALERT/WEBHOOK EXECUTION. NO MERGE TO MAIN. NO POST-OUTCOME RESCUE.**
