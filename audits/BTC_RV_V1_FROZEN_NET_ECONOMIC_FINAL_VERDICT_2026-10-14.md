# BTC REALIZED VOLATILITY V1 — FROZEN HISTORICAL FINAL ECONOMIC CLOSEOUT
Date: 2026-10-14 UTC. Status: **NO_HISTORICAL_CANDIDACY / NO_NEW_OOS / NO_LIVE_GO**.
Authority: user-approved research only, branch `research/btc-realized-volatility-v01-2026-10-14`, draft PR #222. Do not merge main or use broker/private endpoints, wallet, accounts, trading or protected 2026 holdout.

## Pre-outcome chronology and scientific rights
1. **Scientific freeze before market outcomes** commit `c7e7487e17a99a225dcf87423759251d09337405`: fixed 4H completed-bar EMA50 crossover E0, EMA+RV E1, independent RV expansion E2, RV24/RV126 ratio>1.35, exact BTCUSDT USD-M 2021-25 window (2020 warmup), one paper slot/arm, 20% 1x notional, 4% stop, 30d time cap, BASE 8bps taker+2bps adverse slip PER SIDE, STRESS 8+5bps, public timestamped funding no zero-rate substitution.
2. Original QA + source run `38554328926` stopped BEFORE any model outcome on exchange publisher funding header timestamp jitter (milliseconds). Source-only inspection of official Jan 2021 funding archive in run `38554687147` established `calc_time` millisecond additions (2–6ms) despite canonical 8h UTC funding hours.
3. **Source-only amendment freeze before any result** commit `9c2d55e4490b23f5ffc459d3acc12e8c51c77a39`: normalize positive exchange `calc_time` jitter strictly under 1000ms to its preceding exact UTC hour, preserving all original funding rates; no trading rule/indicator/threshold change.
4. Canonical market outcome run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38554979658 (SUCCESS). 7/7 synthetic tests passed, official public price+funding source and engine finished. Historical results archive artifact #11890275593: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38554979658/artifacts/11890275593 .
5. Read-only independently run artifact reporting https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38555635058 (SUCCESS). It downloaded only canonical results and printed exact reconciled economics, no new source/outcome replay.
6. Automation PR triggered an **unintended noncanonical duplicate** market replay run 38555490887 (SUCCESS) with **identical six headline returns/PFs/counts**; no scientific replication/OOS credit. It was not used to select/tune or promote anything. Disabled push/PR-triggered market-workflow automatic repetition afterward (workflow dispatch only on research branch). Preserve provenance instead of hiding the deviation.

## Source data integrity
- 52,608 continuous BTCUSDT USD-M FUTURES official 1h price bars UTC, 2020-01 to 2025-12 complete. 132 official Binance Vision monthly ZIPs with publisher .CHECKSUM verification: 72 market archive files and 60 funding-rate files.
- Exactly 5,478 historical funding events in 2021–25, **0 publisher archived exact settlement markPrice values**. Therefore long funding was recomputed from publisher rates using **market 1h OPEN price proxy**, *not exact exchange mark cashflow*. Important unproven venue economics.
- 2,510 funding event timestamps normalized under pre-outcome bounded source amendment; maximum positive jitter 47ms. Unit checks + checksum source passed. Remaining event/within-hour fill sequence cannot be authenticated at millisecond granularity. No 2026 outcomes ever collected.

## Results — original fixed protocol, independent 10,000 USDT model equity PER arm
| Variant | Closed | BASE return | BASE PF | BASE max hourly-MTM DD | STRESS return | STRESS PF | STRESS max hourly-MTM DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| EMA50 crossover baseline **E0** | **165** | **+10.0892%** | 1.2242 | -14.98% | +8.0053% | 1.1733 | -15.46% |
| EMA50 crossover + RV filter **E1** | **9** | **-1.9659%** | 0.4396 | -3.18% | -2.0596% | 0.4241 | -3.23% |
| RV expansion + trend **E2** | **20** | **+19.6214%** | 3.2321 | -3.97% | +19.3719% | 3.1810 | -4.02% |
BASE / STRESS account return over FIVE YEARS combined, not annual returns, account size 10k virtual, 20% independently risked notional, no leverage.

## Critical economic falsification
- E1 adding the realized-vol filter to the EXACT EMA50 signal is **strictly worse** and only yields 9 trades. It decisively fails all practical profit/frequency predeclared promotion gates; no post-hoc threshold rescue.
- E2 looks visually strong but 20 CLOSED in FIVE YEARS versus predeclared >=60; 2024 n5, 2025 n3 versus fixed >=8 each year. Its strong BASE +1,962.135 USDT is **more than entirely explained by its largest three net winners totaling +2,110.271**: fixed-ledger rest **-148.135**; in STRESS +1,937.191, top3 +2,103.521, rest **-166.329**. NOT a counterfactual resimulation, but severe tail dependence.
- E2 BASE annual closed net 2021 +1,252.594; 2022 -120.097; 2023 +602.382; 2024 +387.780; 2025 -160.523 USD: **3/5 positive years**, below preregistered >=4/5. Not a stable income source. E2 wins 9/20 vs losses 11/20, concentration and sparse sample dominate. E2 BASE funding -359.762 USD; entry fees -36.685; exit fees -38.603, all included in reported PnL.
- E0 EMA baseline independently offers BASE +1,008.921 on 165 trades, STRESS +800.526 but also fails net realized yearly concentration/resilience: 2022 and 2025 negative, static minus top3 -1,258 BASE, and only 3/5 profitable realized exit years. Its +10.09% is not a five-year market edge demonstration.
- The 2021–25 BTC market period had already been analyzed extensively elsewhere in Crypto Lab; no untouched independent OOS credit applies. No independent 2026 forward or public executable venue bid/ask or actual mark funding settlement, no broker stop lifecycle, real min-contract or fills.

## Frozen exact scientific decision
**E1 NO_GO / HISTORICAL_COST_ECONOMIC_FAIL**.
**E2 NO_HISTORICAL_CANDIDACY despite positive BASE+STRESS, because n=20<60, 2024/2025 n<8, 3/5 years positive, top3-removed net<0.** Do not promote to radar, micro-live or automatic trading. Keep immutable as DESCRIPTIVE_TAIL_DEPENDENT but DEPRIORITIZE allocation, no search over RV thresholds/EMA/stop/holding on opened 2021–25 years.
**E0 control is not 'diamond' despite simulated positive returns**; retained as benchmark only.
Final overall: **BTC REALIZED VOLATILITY V1 does not establish an economically robust new incremental edge against EMA50**. Engineering/source audit passed; scientific economic promotion FAILED. This is a completed verdict for this frozen family, not indefinite WAITING, and not a claim every distinct volatility mechanism is impossible.

## Future only via materially distinct mechanism
Researching an event-sourced or venue microstructure signal, or a new independently sourced public volatility feed, requires entirely separate pre-outcome protocol and truly future forward. Do not inherit BVOL7D or RV1 historical PnL, claim a clean 2026 OOS or run further grid searches. Main/real exchange untouched.
