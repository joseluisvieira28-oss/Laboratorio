# CRYPTO LAB — ADVERSARIAL AUDIT: POWER / PREMIA / ENSEMBLE / CEMETERY / STOP
Date: 2026-10-08
Scope: document-only retrospective triage and prospective design. NO new outcomes, trading, main merge, or legacy verdict mutations.
Authority: V2 governance on `crypto-lab-v2-governance-2026-10-07` is DRAFT, not automatically binding on legacy families.

## Definitions and limitation
- `OBSERVED`: number visible in cited GitHub closeout/source receipt.
- `ASSUMPTION`: planning scenario chosen now, **not measured market data**.
- `UNKNOWN`: cannot establish from the accessed receipts alone.
- `UNDERPOWERED_BANKED` can authorize **new genuinely future data under a new freeze** but cannot retroactively delete existing verdicts or claim that a prior unopened holdout was inspected.
- `TEST_AUTHORIZED` requires ex-ante economic hurdle, independently justified design alternative beyond H, nuisance sigma, dependence-adjusted N_eff, power >= target, and earlier source/access gates. N>=some universal number is NOT that test.

## 1 — Five recent, traceable research dossiers (date 2026-10-05 to 2026-10-07)
Selection: five distinct recent dossiers with sourced receipts, not five branches (one family has many branches); branch-wide chronology/exhaustiveness has not been audited.

| Family / relevant stage | Observed independent unit | Evidence | Retro V2 adjudication | TEST_AUTHORIZED proven? |
|---|---:|---|---|---|
| BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001 (V0.2 / V0.3) | Discovery 30 shock clusters from 35 asset-events; 2026 separate holdout only 6 clusters from 29 asset-events | source freeze + holdout closeout | `POWER_UNKNOWN / UNDERPOWERED_SUSPECT`; possible forward bank **only under new authority** | NO — sigma_eff and theta_design not fixed before old outcomes |
| BTC-OPTIONS-VRP-001 executable translation | legacy executable n=19; parent weekly IV-RV observations=192 measure DIFFERENT estimand | V2 freeze + most recent V2 closeout | `UNDERPOWERED_PRE / FORWARD_SOURCE_BANK_REQUIRED`; original 1-BTC weekly alternative N>=30 design is **revoked** for risk-capital estimand | NO — latest direct risk-capital plan revoked / remains underpowered |
| BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001 V0.2 | 24 independent article clusters; 33 trade observations | development closeout | `LEGACY_NEGATIVE_POWER_UNKNOWN` (descriptive effect positive but frozen joint gates fail) | NO — no comparable ex-ante sigma_eff / design alternative documented |
| BINANCE-PERP-MARGIN-TIER-FORCED-DELEVERAGING-001 V0.2 | 30 shock clusters; 98 asset-events, 89 contracts | development closeout | `LEGACY_NEGATIVE_POWER_UNKNOWN` (2023-25 clustered, 90% clusters concentrated in one year; log-score estimand not bps) | NO — ex-ante V2 power missing |
| BINANCE-LISTING-INFORMATION-CASCADE-001 V0.3 | 11 all-metric-evaluable events of required 12 | clean closeout | `SOURCE_BLOCKED`; power is **NOT ADJUDICABLE** with its frozen source design | NO — earlier gate blocked |

The user-supplied illustrative 150–400 independent-event threshold is a *hypothetical event-study planning scenario*, not the V2 rule and not transferable to the funding-premium median, joint log-variance score, options premium, or price-cascade metrics. Under that numeric screen alone, 30/24/30/11/19 < 150; it does **not** convert source-blocked or opened outcomes to canonical UNDERPOWERED_BANKED. **Zero of these five has demonstrated ex-ante V2 TEST_AUTHORIZED in the examined documents.** This is an audit-of-evidence statement, not a claim that all five truly lack power at their economically relevant H.

Sources:
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/binance-funding-interval-regime-shock-v0.3-confirmatory-2026-10-07/research/binance_funding_interval_regime_shock/BFIRS_V02_PRE_OUTCOME_ANALYSIS_FREEZE_2026-10-07.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/binance-funding-interval-regime-shock-v0.3-confirmatory-2026-10-07/research/binance_funding_interval_regime_shock/BFIRS_V03_2026_HOLDOUT_SOURCE_CLOSEOUT_2026-10-07.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/btc-options-vrp-v2-forward-2026-10-07/research/btc_options_vrp_v2/V2_FORWARD_POWER_ACCESSIBILITY_FREEZE.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/btc-options-vrp-v2-forward-2026-10-07/research/btc_options_vrp_v2/V2_RESEARCH_CLOSEOUT_2026-10-07.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/binance-forced-delist-convergence-v0.3-2026-replication-2026-10-07/research/binance_futures_delist_forced_convergence/V02_AUTHORITATIVE_DISCOVERY_CLOSEOUT_2026-10-06.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/binance-perp-margin-tier-forced-deleveraging-v0.2-development-2026-10-06/research/binance_perp_margin_tier_forced_deleveraging/BPMTFD_V02_DEVELOPMENT_CLOSEOUT_2026-10-06.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/binance-listing-cascade-v1-independent-2025-prereg-2026-10-05/research/binance_listing_information_cascade/V03_CLEAN_PRE2024_CLOSEOUT_2026-10-05.md

## 2 — One new premium-class proposal: CS-FUNDING-RISK-PREMIUM-001 (prospective SOURCE/POWER DESIGN ONLY)
**Anti-duplication:** narrowly different from FUNDING-CASH-CARRY-001 (single-instrument, per-asset delta-hedged funding/cost test), from closed spot/perp cash-and-carry, and from generic price-only trend/pattern mining. This is a *multi-asset cross-sectional portfolio receiving a spread in funding compensation* while taking residual basis/short-squeeze/jump/correlation risk. This is NOT a revival of any prior rule, and material distinction must pass a documented Negative Map precheck before data access.

- Payer: levered directional perp demand pays periodic funding when long positioning dominates; receiving side warehouses crowded-position/short-squeeze/liquidation stress.
- Market: Binance USDⓈ-M public historical perpetual data, 2021-01-01 to 2025-12-31, **subject to source-access audit**.
- Universe each rebalance: top 30 contemporaneously eligible USDT-margined perpetuals by **trailing lagged 30-day dollar volume**, age >=90 days, price/funding availability rules frozen. Top 30 is a design, not asserted historical completeness.
- Formation: weekly Monday 00:15 UTC; 7-day completed funding-rate history as of T-15m; short top 10 high carry, long bottom 10 low carry; lagged 30-day daily-vol inverse scaling, each leg capped at 10% gross notional, prespecified dollar-beta neutralization and forced flatten if neutralization impossible; no post-hoc substitutions.
- Hold: weekly portfolio holdings; realized **DAILY** net portfolio returns including marked-to-market, actual timestamped funding, fees, spread/slippage, borrow/margin constraints, delist/relisting handling. Clustering at **calendar day/block** and market-stress regime; a 30-asset day is ONE cross-sectional observation, not 30 independent tests.
- Accessibility: historically replayable account-invariant minimum order/fee tiers, margin, delist closeout, and historical top-of-book execution need verification; never assume public last prices were fillable.
- Hypothesis: mean daily net market-neutral risk-premium return > predeclared H. One-sided alpha=0.05, target power=0.80. Confirmatory 2025 held back only if 2025 was never used for design: if it was, require new post-freeze forward holdout instead.
- Net H policy **ASSUMPTIONS**, not measured: H_lo=1bp/day; H_hi=2bp/day. Design alternative theta_design=6bp/day NET, **ASSUMPTION, NOT FORECAST**. Base/stress cost tiers to be bound to official fee and book-depth receipts prior to outcome access.
- Nuisance daily portfolio sigma_eff **UNKNOWN**. Stress-planning scenarios: sigma_eff=50bp/day or 100bp/day. These are illustrative values, not market estimates. Gaussian iid analytical planning formula with z_(.95)+z_(.80) = 2.48647486: N_eff = [(2.48647486*sigma_eff)/(theta_design-H)]^2, rounded UP.
- Scenario table:
  * sigma=50, H=1: N_eff_req=619 daily observations.
  * sigma=50, H=2: N_eff_req=967.
  * sigma=100, H=1: N_eff_req=2474.
  * sigma=100, H=2: N_eff_req=3865.
- 2021–2025 contains 1826 calendar days (2024 leap), *not necessarily* 1826 usable independent portfolio-days. With hypothetical AR(1) rho=.25, N_eff≈1826*(1-.25)/(1+.25)=1095.6 **only before attrition and heteroskedasticity adjustments**.
- At H_hi=2/theta=6, that 1095.6 could pass only if true portfolio sigma_eff <= 53.25 bp/day; at H_lo=1, <=66.56 bp/day. UNKNOWN until outcome-blind nuisance/source estimates. Fat tails/block bootstrap may increase required power.
- Verdict TODAY: `DESIGN_ONLY / SOURCE_ACCESSIBILITY_UNKNOWN / SIGMA_EFF_UNKNOWN / TEST_NOT_AUTHORIZED`. Calendar horizon sufficient under low-vol assumption, insufficient under high-vol scenario; **historical adequacy UNKNOWN**.

Sources:
- Official Binance historic rate path: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History
- Published cross-sectional *basis* factor research (not validation of this exact funding portfolio): https://doi.org/10.1002/fut.22425
- Crypto Lab negative map: https://github.com/joseluisvieira28-oss/Laboratorio/blob/negative-edge-map-v0.1/negative_edge_map_v0.1/NEGATIVE_EDGE_MAP_V0.1.md

## 3 — Predeclared ensemble, with dead arms included
Candidate research registry K0=9 (proposed, NOT activated):
- Four currently documented Tier-2 *candidate* lineages: BNB-LAUNCHPOOL-DEMAND-001, ETF-CME-INSTFLOW-001, OPTIONS-SPOTPERP-001-V2.1, CED1D-0031 AVAX20.
- Five pre-existing negative control/dead families, unchanged as originally frozen: NFP-SURPRISE-V2; ETF-SHORTFLOW-001; MVE-ADX4H-01; MVE-SIMPLE4H-01; SPOT-PERP-CASH-AND-CARRY-V0.1.
- Historical *thin-margin* economic candidate count: 3 (ETF-CME, OPTIONS-SPOTPERP, CED AVAX20); BNB is a separate tail-fragile candidate. **Verified replayable/forward-eligible weak count = UNKNOWN; confirmed ensemble-eligible now = ZERO.** Nontradable/source-invalid members must be recorded as failed pre-gates, never silently replaced by survivors.
- Frozen inclusion: ALL 9 declared ex ante; source/cost/reproducibility gate before any evaluation; if required member is absent, do not report a post-hoc 8-member ensemble as primary. A newly frozen lower-N alternative is an additional counted trial with new future data.
- Uniform daily UTC valuation of all valid streams; no hindsight fill. Lagged 60d realized-vol target per strategy, equal 1/K risk weight, risk caps, same portfolio cost friction; missing trading is actual zero exposure, missing data is INVALID and cannot be silently imputed as flat. Weekly rebalance, no optimized weights.
- |rho_pair| < 0.30 threshold estimated ONLY on a frozen pre-evaluation calibration sample; for any pair above threshold, PRIMARY ENSEMBLE BLOCKED (no post-hoc member deletion). Correlations during market crises are a separate compulsory stress check.
- DSR/selection ledger: all 9 members, all previously tried model variants, all pretests and ensemble specifications. The Negative Map documents Pattern Lab 3600 hypotheses + AggTrades 240 variants = at least 3840 raw distinct search shots in just those two screens; number of effective independent DSR trials is **UNKNOWN**. DSR itself UNKNOWN without returns/T/skew/kurtosis/trial variance and selection dependence.
- Illustration ONLY, not measured returns: identical vol, mean rho=.20 (<.30), 3 weak each annual net SR=.25, BNB SR=.40, 5 dead controls each SR=-.10. Average member SR = (3*.25+.40-5*.10)/9=.07222. Equicorrelated K_eff=9/(1+8*.20)=3.4615; SR_ens = .07222*sqrt(3.4615)=.13437 annualized. No reason to believe the true portfolio earns this positive figure; this is a transparent hypothetical. For three weak-only hypothetical, SR=.25*sqrt(3/(1+2*.20))=.36596, but that is NOT admissible as the official nine-arm primary if chosen by old outcomes.
- Status: `ENSEMBLE_DESIGN_ONLY / CORRELATIONS_UNKNOWN / DSR_UNKNOWN / TEST_NOT_AUTHORIZED`.

Sources:
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/negative-edge-map-v0.1/negative_edge_map_v0.1/EDGE_PRIMITIVE_MAP_V0.2.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/negative-edge-map-v0.1/negative_edge_map_v0.1/NEGATIVE_EDGE_MAP_V0.1.md
- Deflated Sharpe Ratio methodological publication: https://doi.org/10.3905/jpm.2014.40.5.094

## 4 — U95 >= H cemetery count
Answer: **UNKNOWN / UNKNOWN** (numerator/denominator).
- 2026-09-27 Negative Map historical snapshot = 68 board *rows*: 26 NEGATIVE_SCIENTIFIC, 9 POSITIVE_OR_SURVIVES, 1 MIXED, 10 INSUFFICIENT_SAMPLE, 15 BLOCKED_OR_TECHNICAL, 7 PENDING_OR_FORWARD. Later primitive-map reconciliation states 70 rows. Neither number is total unique closed branches/families and neither has H + compatible U95.
- DO NOT calculate U95 from new protected outcomes. Read ONLY already public/archive **summary receipts** and frozen historical preoutcome economic H.
- Inventory schema per economic_family_id + scientific_claim_id + frozen_rule_hash + parent_run_id, primary estimator type/unit, N_raw/N_cluster/N_eff, date, H_original, sigma/SE/HAC/bootstrap U95 (same estimator/units/direction), costs & risk charge, existing verdict, lineage, outcome-access status.
- Condition: `eligible = closed_and_outcomes_already_opened_and_H_was_pre-frozen_and_U95_compatible_available`; `count_true = sum(eligible & U95 >= H)`, separately record missing-H, missing-U95, mismatch, source-blocked, duplicate branches, and original negative/positive verdict.
- U95>=H means **old data could not exclude an economically relevant H**; it is NOT survival or evidence of positive edge.
- If U95 cannot be recovered from old sealed summary receipt, label UNKNOWN, never reopen holdout to classify.
- Audit first on any suitable closed families; a census requires exhaustive branch-to-family deduplication and a manifest locked in advance.

Sources:
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/negative-edge-map-v0.1/negative_edge_map_v0.1/NEGATIVE_EDGE_MAP_V0.1.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/negative-edge-map-v0.1/negative_edge_map_v0.1/EDGE_PRIMITIVE_MAP_V0.2.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/crypto-lab-v2-governance-2026-10-07/research/crypto_lab_v2/LEGACY_CEMETERY_READJUDICATION_PROTOCOL_V0.1.md

## 5 — Objective stopping rule PROPOSAL, not a V2 mandate
Accept possibility of no accessible edge in a *narrow, pre-enumerated, homogeneous mechanism class*.
- Operational pre-gate: refuse new trials without independently justified economic payer, source viability, cost headroom, and prospective power.
- Confirmatory stopping rule for ONE homogeneous class: after **46** genuinely distinct, pre-registered, source/access PASS, independent economic families (or non-overlapping real replications), if **zero** obtain both frozen SURVIVES_AT_H and new-independent forward confirmation, stop opening new families in THAT class. Require at least 80% power for the Development step AND at least 80% conditional power for independent Forward confirmation at the design alternative. No pre-gate failures or branches/parameter variants count as a powered family.
- Derivation: Null benchmark q>=10% accessible-true-edge incidence; each powered test detects with **two independent** >=80%-power stages per true edge yield an end-to-end detection probability >=.8*.8=.64; probability of 0 fully confirmed detections in 46 independently exchangeable tests at q=.10 is (1-.10*.64)^46 = .0477187. Hence 0/46 excludes q>=10% at ~95% **only** if both-stage power, exchangeability, and independence assumptions actually hold. If the 80% power were already an end-to-end property, 36 would suffice, but that must NOT be inferred from a single-stage V2 receipt.
- If class has 1+ confirmations, do not use 0/36 rule; update beta-binomial/effect-size model and freeze a separate decision.
- Economic override: immediately stop when remaining expected marginal research value < research/opportunity cost, regardless of count (operational SEARCH_STOPPED_ECONOMICALLY, not "proof no edge in crypto").
- Today N_powered_forward_confirmed_count for any putative homogeneous class = **UNKNOWN**: historical 70 board rows are not 70 independent 80%-powered confirmed-family tests.
- Claims must be class-restricted; never generalize to "no crypto edges exist".

Sources:
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/crypto-lab-v2-governance-2026-10-07/research/crypto_lab_v2/CRYPTO_LAB_V2_GOVERNANCE_FREEZE_2026-10-07.md
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/crypto-lab-v2-governance-2026-10-07/research/crypto_lab_v2/CLAUDE_DEEPSEEK_METHOD_ADJUDICATION_V0.1.md

## Status / evidence integrity
Research document only; scenario computations are explicit model assumptions, never reported as empirical alpha/power. Legacy closeouts unchanged. No source or market outcome was opened as a result of authoring this audit. No new trade or exchange/account mutation authority.
