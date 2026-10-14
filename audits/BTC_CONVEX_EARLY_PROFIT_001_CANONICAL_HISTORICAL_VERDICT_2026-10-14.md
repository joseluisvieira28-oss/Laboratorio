# BTC-CONVEX 1H + Early Profit 001 — CANONICAL 2020–2025 historical retrospective verdict
2026-10-14 UTC. **FULL CAUSAL HISTORICAL REPLAY PASS / EARLY_PARTIAL_COSTED_HISTORICALLY_WORSE / NO NEW OOS / NO LIVE GO.**

## Scientific provenance and exact results
- Operator prior preference and +1R/50% reduction +0.25R net cash gate frozen before outcomes at `c72ab51164998bc0d12552c25ee138f8f6d5cd63`; [full cemetery replay queue](../research/operator_risk/EARLY_PROFIT_HISTORICAL_CANDIDATE_QUEUE_FREEZE_2026-10-14.md) freeze `72f8eb50724ab449925632bce1a3fea1f42003d0`. 2020–25 BTC data were already studied, zero new holdout credit.
- Matched parent exact pinned `research/payoff-40-10-btc-engine-2026-10-13` commit `2e68dbce5705e4d285f6805933768878fb34dea1`, original parent 1h V5 unchanged. Complete public Binance USD-M source with publisher SHA256: 2020-02 through 2025-12 1h price + mark-price proxy bars + archived historical funding; exact original reported baseline preserved.
- Child has separate 20%-notional paper portfolio, same parent entry signal and fees, no leverage. +1R historical SOURCE TRANSLATION: verified *completed* 1h candle close >+4% from entry, at following 1h open propose 50% partial iff closed-half modeled cash net >=0.25 ORIGINAL full net R budget; rest stop protected next interval, tightening to funding+fees-adjusted BE only at fully completed bar close. Stop never loosens even before partial. Historical 1h OHLC next-open fills are NOT executable historical bid/ask. No real broker stop ACKs or venue order min-lot proof.
- On code inspection **before accepting model outcome**, prior run #38580448164 rejected NONCANONICAL because Child accidentally inherited nonmonotonic Parent stop reset. Child stop fix `92d807c211e61fc3e66f5dcaabb3029694ab4122`, documented under separate source-only correction; 39 synthetic regressions passed. Only post-fix canonical [run 38581197237](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38581197237) SUCCESS, archive [artifact 11903820922](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38581197237/artifacts/11903820922), original publisher source SHA JSON `7f4a7f7e4e3c8c062fb6ef2c04f0974c0304067da090a278c4e18f854b07f7b9`; comparison JSON `aa56fbbb92e2bb46c836589f9a8205fd86035a5b6fcb007050b9a484058cd43e`. Independent READ-ONLY artifact audit [run 38583007211](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38583007211) SUCCESS; no additional market replay was needed for final decision. Later automatic historical repeats disabled in workflow to avoid nonindependent duplicate credit.

| 2020–25 model | Parent BASE | 50%-Early BASE | Parent STRESS | 50%-Early STRESS |
|---|---:|---:|---:|---:|
| Cash equity return (open position still possible) | **+32.4559%** | **+8.7854%** | **+30.5913%** | **+6.2169%** |
| Closed positions | 89 | 119 | 89 | 120 |
| Net PF closed | 1.4469 | 1.1558 | 1.4179 | 1.1085 |
| Partial-50% realized positions | not applicable | **56** | not applicable | **56** |
| Model hourly-close max drawdown | **-14.06%** | **-11.81%** | **-14.33%** | **-12.59%** |
| Signed funding paid total USDT | **-1656.74** | **-714.54** | **-1646.19** | **-708.05** |
| Static net closed after top3 removed | not independently reaudited this run | **-855.97 USDT** | not independently reaudited | **-1102.80 USDT** |

**DELTA EARLY MINUS ORIGINAL: -23.6705 percentage points BASE and -24.3743 pp STRESS**, with a relatively modest ~2.25pp BASE reduced maximum hourly-close drawdown. This child preserved a small positive cumulative historical model return but DESTROYED most of the original trend tail and has low PF. 56 realized half trades are not 56 final guaranteed profitable whole positions; total result includes losing remainders and larger frequency of final exits and opportunity changes. Funded margin/actual venue economics are not certified.

## Year/model interpretation
Parent BASE model had losing cash-equity years 2022 (−9.10%) and 2025 (−6.45%); child also lost 2022 (−6.96%) and 2025 (−4.23%). 2024 gain Parent +19.70%, child +11.50%; large winner truncation consistent with result but never retroactively optimize a rescue target.
One position at end-of-2025 remains open in both models. Parent last-close unrealized net if liquidated at close approx -22.15 USDT BASE; child separately marked terminal +8.6641% BASE, +6.0879% STRESS. Do NOT claim realized equity equals terminal including open exposure. Risk model uses 1h lows/opens, cannot prove stop-market fill in outages, liquidation or price gaps.

## Exact frozen decision
**EARLY-PROFIT-HARVEST-001 BTC-CONVEX 1H, same 2020–25 sample: NEGATIVE INCREMENTAL MODEL ECONOMICS VS PARENT, NO_PROMOTION.** The math supports user's preference to realize some gains but does not support replacing this Parent's exit with this particular +1R/50% historical strategy. No optimization of +1R/50%/0.25R following these opened outcomes. Original Parent unchanged and also NOT trade-ready.
Proceed exactly frozen ordered alternatives SOL1h and BNB4h; signed separate public source-only replay; no main, 2026, orders, private endpoints, wallets or payments.
