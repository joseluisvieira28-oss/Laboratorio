# SOL-CONVEX 1H + BNB-CONVEX 4H — Early Profit V1 frozen historical full-model closeout
2026-10-14 UTC. **TWO HISTORICAL SOURCE/CONTROL PASS / COMBINED EARLY-HALF+MONOTONIC INCREMENTAL RETURNS NEGATIVE IN BOTH BASE AND STRESS / NO NEW OOS / NO LIVE GO.**

## Pre-outcome chronology and immutable receipts
- Priority ordered and early cash extraction rules frozen in [queue](../research/operator_risk/EARLY_PROFIT_HISTORICAL_CANDIDATE_QUEUE_FREEZE_2026-10-14.md) before original BTC child; original ETH/alt candidate shortlist SOL1h and BNB4h fixed before these child price outcomes.
- SOL & BNB historical specific mapping freeze [EARLY_PROFIT_SOL_BNB_HISTORICAL_PREOUTCOME_FREEZE_2026-10-14.md](../research/operator_risk/EARLY_PROFIT_SOL_BNB_HISTORICAL_PREOUTCOME_FREEZE_2026-10-14.md) commit `a9a873a010afd6b6ef36d9e056852da4ccd22a0a`; code/QA source pinned historical Parent SHA `42d6748864dd78b911b5f1fc775ff1950b556d2b` (PR #215). No tuning after outcomes.
- Correct original 2023–25 5m canonical 333,216 OHLCV bars + 27,768 independent 1h + 3,288 dated funding receipts per instrument, full publisher `.CHECKSUM` SHA256, warmup 2022 Nov-Dec, 2026 excluded. All publication/source/control gates PASS.
- Canonical run [#38583007342](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38583007342), **both SOL and BNB jobs SUCCESS**; SOL source+trade-ledger [artifact 11902974657](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38583007342/artifacts/11902974657); BNB [artifact 11904242578](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38583007342/artifacts/11904242578). SOL REPORT SHA256 `f0de0902dc30195665d08db070ca4759fe8956ceed365056535aa3acd8e979c4`; BNB `cf1f6323d67f79150c01d3dfd14fb245a58a729c2ddb21c1d81fd9c310ba9818`.
- Base strategy: unchanged original V5 long trigger/20%-notional/4% stop/+5% completed TF close 12%-from-peak nonlatched trailing; BASE 8bps taker +2bps slip PER SIDE, STRESS 8bps+5bps each; historical market 5m price and observed funding paid using 5m market price proxy, NO actual MEXC exchange fills.
- Separate fully recomputed early Child (not static subtraction) realizes 50% when +1R favorable is confirmed by completed 5m close, first NEXT 5m OPEN and >=0.25R modeled net closed cash, then fee/funding-aware remaining BE and monotonic stop. Historic 5m MARKET OPEN is **NOT verified executable bid/ask**, simulated exchange stop acknowledgement NOT proven. Fractional half minimum contract feasibility unverified.

## Results by independent simulated asset/portfolio, 2023–2025 CUMULATIVE NET modeled terminal marked % (not annual)
| Symbol + scenario | Original Parent | Early-half + monotonic | Difference | Parent closed | Child closed | Child realized-half events | Original PF | Child PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **SOL1H BASE** | **+59.3883%** | **+18.7648%** | **−40.6235 pp** | 84 | 106 | 55 | 1.8240 | 1.3879 |
| SOL1H STRESS | +58.2955% | +15.2599% | −43.0356 pp | 84 | 106 | 53 | 1.8066 | 1.3091 |
| **BNB4H BASE** | **+27.3779%** | **+10.3178%** | **−17.0601 pp** | 28 | 34 | 19 | 2.8942 | 1.8001 |
| BNB4H STRESS | +27.0553% | +10.1231% | −16.9322 pp | 28 | 34 | 19 | 2.8608 | 1.7804 |

Conservative 5m LOW model drawdown: SOL Parent BASE -12.27% vs Child BASE -8.83%; BNB Parent BASE -7.96% vs Child BASE -6.93%. That safety improvement was materially smaller than the modeled long-run profit sacrificed.
Both children remained model-profit-positive over these already-selected years. That is **not evidence of new net alpha**: they are materially worse than the matched original parent, and historical selection bias exists. No 2026 protected holdout, no live realistic limit/taker fills, no venue exact funding mark, no market-to-market settlement guaranteed.

## Precise attribution and policy decision
**The CHILD changes TWO coupled elements:** (a) early 50% cash exit + subsequent net-BE remaining stop, and (b) 'stop cannot loosen' compared with the original Parent whose V5 close-trigger trailing deactivates. This comparison DOES NOT isolate the contribution of early-half alone and must NEVER be sold as such. It answers whether the operator's combined chosen conservative exit package enhances the historical economics; in these three studied trend families the answer so far is NO.
Expected risk benefit is supported in historical low-bar/proxy DD but independent calibrated future risk tail and real stop order ACK unavailable. No 'looser/earlier at +1.5R' post-outcome repair of these three exact policies. Keep original trend mechanisms as historical leads, keep operator policy as preference, and do not conflate preference with economically proven improvement.

Next frozen queue: BTC PAYOFF original 4R target / -10% margin stop, standalone full historic target-plus-half comparison. Any new event-driven BNB Launchpool or BTC->SOL liquidation child requires ORIGINAL strategy-specific protective stop, venue data and fresh freeze before attempting +1R; cannot infer R from a 24h event return.
