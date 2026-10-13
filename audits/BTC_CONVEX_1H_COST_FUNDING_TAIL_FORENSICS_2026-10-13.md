# BTC-CONVEX 1H — FUNDING, COMMISSIONS, WINNER-TAIL: ECONOMIC FORENSICS
**Closeout dated 2026-10-13.**
**Standing authority:** RESEARCH ONLY; existing historical BTC 2021–2025 known, zero independent OOS, zero real venue fills and zero trading.
**Pre-outcome forensic freeze:** `research/btc_convex_1h_forensics_20261013/PREOUTCOME_FORENSICS_FREEZE.md`, commit `dd7bb1433891ca337920265a3dd6a4429c06c600`.
**Source:** immutable prior canonical 5m V02 run 38426153613 artifact 11828479302. Original code and 1h trailing unchanged.
**Validation:** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38427855128 **SUCCESS**; 6 synthetic accounting invariants passed; both original 1h_BASE and 1h_STRESS trade ledgers fully reconciled row-by-row, including open-position cash residue.

## Identifiable prior historical net components, identical 1h trades
| Closed ledger 2021–2025 | BASE | STRESS |
|---|---:|---:|
| Closed trades | 77 | 78 |
| Winners | 17 | 17 |
| Price-only realized PnL, AFTER assumed slippage | +2,954.116754 | +2,805.220738 |
| Closed entry and exit fees | -276.379212 | -278.610591 |
| Closed funding at prior **market-price proxy** | -1,150.590528 | -1,145.735928 |
| **Closed net PnL** | **+1,527.147014** | **+1,380.874220** |
| Accounting cash residual from remaining OPEN trade | -5.514264 | -5.443205 |
| End realized paper cash equity | 11,521.632749 | 11,375.431015 |
| Final OPEN position mark-to-market PnL, not closed | -14.196642 | -14.694803 |
| End total *marked* paper equity | **11,507.436107** | **11,360.736211** |
All in USDT, starting paper capital 10,000. Closed ledgers differ from total cash totals because one trade remains open. V02 1h BASE terminal mark return +15.074361%, STRESS +13.607362%. The observed static funding debit of the closed ledger is 4.163 times the observed closed fees; substantial relative to fees, but settlement mark is NOT independently certified.

## Static, unchanged trade-ledger cost sensitivities, BASE (NOT backtests / portfolio reruns)
| Hypothetical ledger accounting | Closed net PnL USDT |
|---|---:|
| Original fees and funding | +1,527.147014 |
| 50% recorded fees | +1,665.336620 |
| 0 recorded fees | +1,803.526225 |
| 0 recorded funding | +2,677.737542 |
| 0 recorded fees AND funding | +2,954.116754 |
| Extra +2bps each side | +1,458.052211 |
| Extra +5bps each side | +1,354.410006 |
| Extra +10bps each side | +1,181.672999 |
These are fixed-trade accounting arithmetic, not future executable fills or capital-compounded causal runs. Zero funding/fees is an unattainable *accounting upper scenario*, not proposed alpha or estimated exchange fee tier. The change in sizing, skipped trades and bankruptcy risk is NOT recomputed.

## Timing and asymmetric tail
- Median closed trade duration BASE **3.21875 days**; longest **110.003472 days**.
- Closed-trade funding cost on 69 trades, positive funding cashflow on just 2; largest single funded cost **-195.553568 USDT**. Some other trades have zero funding.
- Positive net closed trades BASE 17/77 = **22.08%**.
- Top1 net winner **+1,134.103198 USDT**, top3 net winners **+3,095.425042 USDT** (42.489% of all gross positive winners), top5 **+4,610.173150 USDT** (63.281% of gross positive winnings).
- Static removal of top3 from preexisting closed trade results: **-1,568.278029 USDT**; THIS IS NOT a hypothetical portfolio re-run or optimal exit.
- Per-exit-year closed PnL: 2021 +1,083.814071; 2022 -996.773915; 2023 +349.557048; 2024 +1,889.690568; 2025 -799.140758. Exactly 3 of 5 positive accounting years, not a recurring salary source.

## Immediate falsifications and next scientifically legitimate source step
1. **Fee engineering alone is SECONDARY**: half fees adds only 138.19 USDT to the fixed 77-trade ledger versus -1150.59 USDT modeled funding, without preserving execution quantity/queue. Maker-limit execution may miss entries or large winners; never claim a free maker fill.
2. **Funding is first-order but model-dependent**: the historical funding rate series is public, yet the used cashflows rely on 5m *market open*, not contemporaneous exact funding settlement mark, account/venue position rules or effective rebates. No authority to suppress funding arbitrarily by shortening holds without new prospective test (shortening may eliminate the very right-tail winners). Priority is timestamp-correct verified settlement mark/funding source and per-trade funding provenance, then a matched prospective economic protocol.
3. **Protection risks killing convexity:** the 1h edge is highly dominated by few large winners; locking profits aggressively can turn winners into small wins and remove more right-tail than saved. Do not retune trailing 12%, activation 5%, or stop 4% using the already observed years. Audit original per-trade MFE vs closed exit first, and reconcile prior H1 sticky-trail findings; any new exit hypothesis must be preregistered and independently tested.
4. No continuation to real orders. A prospective observer with append-only *point-in-time* quotes + mark/funding + fill feasibility and truly untouched events is required to promote. 2026 holdout stays locked.

**Verdict: MODEL CASHFLOW RECONCILED / FUNDING COST FIRST-ORDER / FAT-TAIL DEPENDENCE PROVEN DESCRIPTIVELY / NO NEW ALPHA / NO MICRO-LIVE GO.**
