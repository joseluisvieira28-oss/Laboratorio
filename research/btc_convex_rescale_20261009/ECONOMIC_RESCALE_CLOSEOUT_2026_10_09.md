# BTC-CONVEX V5 — LOWER-RISK POSITION SIZING, SAME CONVEX WINNERS — HISTORICAL CLOSEOUT
Date: 2026-10-09, research-only.

**Scientific classification**: `HISTORICAL_LOCAL_POSITIVE_AFTER_RESCALE` on the previously exposed 2021–2025 ETH/SOL/BNB trade ledgers; `HISTORICAL_CROSS_SECTION_GENERALIZATION_FAIL` (0/5 expansion basket); `TAIL_DEPENDENCE_FAIL` (2/3 preferred small-risk sleeves negative if three highest-*percentage*-return historical winners never fill); `ACTUAL_EXECUTION_UNVERIFIED`; `REAL_CAPITAL_GO=NO`.

## Actual work performed and provenance
- Created isolated branch `research/btc-convex-size-risk-stress-2026-10-09` from existing historical-only audit, no `main` change.
- New frozen pre-computation science document `PRE_COMPUTATION_RESCALE_FREEZE_V01.md`, commit `5432640e54e7ed92fcfb0eeea12dbfc7c20305bd`, BEFORE first rescaled economic result.
- Real market outcomes in the source 2021–2025 archived tapes were ALREADY OPENED prior to this freeze. This study CANNOT become independent/OOS merely by pre-freezing new sizing arms.
- Original historical Parent V5 first-basket 2021–2025 canonical artifact 10775714534, expansion 10778258822, 3rd Parent/H2 10791006099; original BASE 10bps commission each side plus 2bps adverse slippage per side; STRESS 10bps commission + 5bps adverse slippage per side; actual *historical* perpetual funding as carried in original trade ledgers.
- Committed a deterministic independent ledger-resizing script `rescale_original_trade_ledgers.py`; checks original asset universe, source hashes, chronological order, original known 95%-allocation compounding replay, and intact original generalization FAIL verdict.
- Fail-closed technical run 37893743955: source receipts do not store `qty`; resolved via original `return_pct` validated by quantity reconstructed from `commission/(0.001*(entry+exit))`, amendment preserved as `TECHNICAL_LEDGER_NORMALIZATION_AMENDMENT_2026_10_09.md`. ZERO scientific credit to this failure.
- Fail-closed technical run 37893875251: assumption BASE/STRESS contain identical trade chronology was false for SOL, since adverse slippage changes the stop/outcomes; corrected by reading each original frozen layer as its own original tape, amendment `TECHNICAL_LAYER_PATH_AMENDMENT_2026_10_09.md`. ZERO scientific credit to this failure.
- **Final frozen-content run 37893974992: SUCCESS**, on commit `8d2106583564d0df81961bd6ae1b3531cc85bd33`. Artifact ID **11598844622**, `btc-convex-rescale-risk-stress-v01-37893974992` (JSON full matrix all 13 parent assets, all arms, BASE/STRESS and adverse cases). Five synthetic invariants passed.
- No new raw candles downloaded; no newly opened 2026 holdout; no exchange account reads or orders.

## Sizing geometry, original execution untouched
Original source used 95% current account allocation for each independent asset, with 4% underlying initial stop. Nominal account risk on ideal stop ~3.8% *before* cost/gaps.
Fixed new arms replace 95% notional with:
- 0.25% *nominal price stop* budget -> 6.25% current sleeve equity notional;
- 0.50% -> 12.50%;
- 1.00% -> 25.00%.
No altered entry/exit timestamps, stops, signals, leverage rescue or future event. Trade NET per notional is taken from original position, fees and funding already included, assumed linear in quantity with **no depth/market-impact/lot/venue validation**. Each asset is an independent separate original 10,000-USDT research sleeve. Not a shared account or actual 3-asset portfolio.

## BASE historical results of original 2021–2025 Parent V5 (per sleeve)
| Nominal 4%-stop risk | Allocated notional | ETH total 5yr | SOL total 5yr | BNB total 5yr | Worst *closed-trade-only* DD across ETH/SOL/BNB |
|---|---:|---:|---:|---:|---:|
| Original ~3.8% equity nominal | 95% allocated as original | +96.12% | +91.23% | +255.84% | −55.12% |
| 0.25% | 6.25% | +8.54% | +11.34% | +14.00% | −4.44% |
| 0.50% | 12.50% | +17.08% | +22.59% | +28.85% | −8.70% |
| 1.00% | 25.00% | +33.82% | +44.03% | +60.81% | −16.73% |

*These are returns over all five historical years, NOT returns per year.*
At 0.50% nominal risk, respective BASE annualized CAGR ETH **3.20%**, SOL **4.16%**, BNB **5.20%**; worst observed per-trade fraction of its pretrade sleeve equity **−0.817% / −0.661% / −0.794%**, larger than the ideal nominal 0.50% risk due original trade path, costs and gaps. This is evidence a 0.50% *planned* stop is not a 0.50% *guaranteed* account loss bound.

**Critical drawdown warning:** ALL above DD figures are **closed-trade realized-equity path DD only**. They are NOT marked-to-market DD, which can be larger while a position is open. Original 95% BASE bar-path MTM DD was ETH −54.28%, SOL −58.97%, BNB −58.20%. New low-risk MTM DD was not recomputed from candle paths; DO NOT claim that low-risk dynamic 4% or 8% DD is a proven intratrade maximal loss.

## Economic stress 0.50% nominal risk
| 2021–2025 over five years | ETH | SOL | BNB |
|---|---:|---:|---:|
| BASE frozen original commission/slip/funding | +17.08% | +22.59% | +28.85% |
| STRESS original, slippage 5bps vs BASE 2bps each side | +16.50% | +22.76% | +27.53% |
| STRESS plus hypothetical additional 10bps/roundtrip | +15.06% | +20.29% | +25.90% |
| BASE, **three biggest percent-return winners missed** | **−3.15%** | **−4.63%** | **+0.71%** |

- Baseline and **+10bps cost stress** remain positive 3/3 in the original favorable basket, but the adverse 2021–2025 independent expansion remains **0/5 positive**, no cross-sectional generalization.
- In the BASE top3-missed experiment, the original 3 biggest *percentage* winners were assigned 0 return at their historic timestamps and equity was re-compounded, holding all other trade times/outcomes. This is a theoretical missed-entry stress, not executable fills or a valid price-path counterfactual. Original previous report's negative after *three biggest dollar-PnL winners* for BNB is a DIFFERENT sensitivity; both must be disclosed and not conflated.
- Smaller risk is math, not alpha: 0.25% risk returned only ~1.65% (ETH), 2.17% (SOL) and 2.66% (BNB) annualized in the favorable original period, before operational issues, direct book-depth constraints and any additional overhead.

## What is NOT improved by reducing notional
1. Signal predictive quality, cross-sectional discrimination, negative 0/5 replication, or original 2026 V0.2 losses (3/3 resolved negative; source replay rather than point-in-time fill).
2. Rare-trend winner dependence: ETH/SOL lose money over five years if three BASE historical top-%-return winners are missed.
3. Exchange/minVol accessibility and actual 2026 account-specific fee, quote/spread/size at entry, margin, latency and stop-gap tail risk.
4. Correlation and total wallet risk: ETH/SOL/BNB trade sleeves are independent simulations and may be exposed simultaneously. Summing nominal 0.50% across three implies up to **1.50% initial-stop nominal equity risk** in a common-wallet conceptualized allocation if each uses full wallet sizing; actual correlation/gaps can magnify.
5. Original 95% vs resized performance comparison is in the SAME already opened historical dataset. The variant is a conservative risk diagnostic, NOT a newly "scientifically approved general trading engine".

## Recommendation / next true attack
**Do not increase risk to 1% just because it printed a higher historical CAGR; it exhibited −16% to −17% closed-trade DD before considering intra-position MTM.** 0.25% is materially gentler, but under the favorable historical period only ~1.7–2.7% annualized before further costs. 0.50% is a more informative *research sensitivity*, not a recommended funded sizing policy, with ~3.2–5.2% simulated annual CAGR and ~8–9% closed-equity drawdown.
The scientific bottleneck is NOT sizing any longer: determine actual executable net after marketable **entry/exit** source and historical source at decision time, minimum contract size with low nominal capital, and whether >0 after missed winners across predeclared independent markets/time partitions (not repeated retrospective threshold choices). Only one genuinely new hypothesis plus untouched data should ever justify later broad economics claims.

## Links
- Run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37893974992
- Artifact https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37893974992/artifacts/11598844622
- Parent original 2021–25 first basket https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35918769969
- Parent expansion original https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35921780080
- Parent third basket original https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35956632021

Safety: NO live orders, capital, private auth, wallets, account reads, exchange mutations, money spent, main merge, Render/production mutation, post-outcome strategy parameter tuning, or reopened protected 2026 outcomes.
