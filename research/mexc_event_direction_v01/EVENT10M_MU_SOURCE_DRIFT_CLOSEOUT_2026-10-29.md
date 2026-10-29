# EVENT-10M MU — SCIENTIFIC CLOSEOUT / SOURCE DRIFT
Date: 2026-10-29. Research-only. NVIDIA deliberately excluded; SPCX excluded (no Nasdaq-listed underlying opening auction); MLIUSDT not assumed MU.

## Product hypothesis
Micron Technology publicly trades on Nasdaq as MU; MEXC product MUSTOCK_USDT represents MU as a separate standard-futures price index. Investigate rare US 09:30 ET opening situations in which a *causally available* Micron price signal is ahead of the MEXC Event Futures index for a future 10m event. This has **not** been demonstrated.

## Completed source evidence — PR #284
[Actions run #40905532432](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40905532432), head eeeb5f01b76cbd7ec8736f175ce35e86add6d432. MU Yahoo public UNOFFICIAL 1m chart and MEXC MUSTOCK_USDT public standard futures INDEX Min1 both provided 40/40 same minute starts each day for Oct26 and Oct27 in 09:30–10:10 America/New_York (13:30–14:10 UTC, US DST still on). Source format and historical coverage PASSED. This DOES NOT prove stock feed collector availability at actual time, event contract payout, or exact executed MEXC entry-price parity.

## New fixed mechanism — PR #285
Pre-frozen ten scheduled nonoverlapping 10-minute decision slots across two days. MU stock 2-minute sign from completed bar CLOSE[t-3min] vs CLOSE[t-5min], versus MEXC standard index OPEN[t-3min] vs OPEN[t-5min]. Only disagreements qualify, choose MU sign; agreement/no movement -> abstain. Matched baselines always-UP/always-DOWN/MEXC momentum. Index OPEN[t+10] versus OPEN[t] is proxy target. q=0.80/0.85 hypothetical, not historical MEXC payout. No model fitting/tuning. Even perfect 10/10 would be vastly underpowered.

## Three immutable run outcomes, no economic labels opened
1. [V0.2 run #40905998844](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40905998844) failed at first Yahoo full-JSON SHA check BEFORE opening any index outcomes. Yahoo raw SHA had changed vs gate #40905532432.
2. [V0.2.1 independent canonical SOURCE-ONLY run #40906251352](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40906251352) repeated both Yahoo and MEXC responses twice: **60/60 matched 1m timestamps** each day during 09:30–10:30 ET, source schema PASSED. Raw Yahoo JSON SHA changed even between immediately repeated calls, while canonical sorted minute+price digest was identical WITHIN this run. Pre-outcome canonical SHA: Yahoo MU CLOSE aea2418b3308cec57eb1480fcf847ab9e4b82f2f9091b72a8eb14770dfcb6c5d; MEXC index 26 Oct a950a8fef646d3773cd415e13a10c55d2e35cbef608bcfa1b02752aa149c884a; 27 Oct a93f2e96071080ff7769aea2665353a28509623a099928181b4af2341b1c00a3. This is source feasibility and one-run reproducibility only, not a guarantee of stability between jobs.
3. [V0.2.2 run #40906474367](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40906474367) checked the frozen canonical digests. Yahoo MU CLOSE **CHANGED AGAIN** to fb5f745b4dde9fd611199de115302401f8c0bcb411ae3bed6e58dbe708062733. Code failed closed before MEXC target, signal outcomes, payouts or backtest. Root cause of the canonical difference was NOT isolated to particular minutes or fields. Do not call it a confirmed Yahoo revision or overwrite the previous scientific freeze.

## Verdict
**SOURCE_DRIFT_BLOCKED / PRICE_HISTORY_NOT_REPRODUCIBLE_ACROSS_RUNS / DIRECTIONAL_OUTCOMES_OPENED=0 / EDGE_NOT_TESTED / NO_LIVE_GO.**

Need a trustworthy authorized as-of source for MU minute quotes, snapshots with immutable externally anchored receipt timestamps and source publication latency. Distinguish historical changes from data transformations before reopening V0.2 as a NEW explicitly frozen study; do not just reset the hash to the next observed value. Verify MEXC Event Futures current direction-specific payout and actual order entry price, not just the standard-index proxy. Sep2026 holdout remains sealed. No user/NVIDIA duplication, private endpoints, orders, account reads, money, main merge or trading.
