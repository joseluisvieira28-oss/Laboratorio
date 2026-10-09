# MEXC-CONVEX-V01 — FIRST CAUSAL GATEWAY CLOSEOUT
Date: 2026-10-09
Status: **SOURCE_GATEWAY_PASS_NO_TRADING / TIMELY_SIGNAL_OBSERVATIONS=0 / ECONOMIC_EDGE_NOT_TESTED**
Mode: public read-only source/signal diagnostics. NO real orders, accounts, wallets, fees charged, capital or main merge.

## Pre-freeze, authority, code and run
- Research branch: `research/mexc-convex-v01-causal-gateway-2026-10-09`.
- Exact pre-sample freeze path: `research/mexc_convex_gateway_v01/MEXC_CONVEX_V01_CAUSAL_GATEWAY_PREFREEZE_2026_10_09.md`, commit `63464fc8b04d45700a96360a03dfcc2732668e53`, published before the code's first public source evaluation.
- Code SHA commit `b25804559236da2926f1dfec9ac2b11ee8584bb1`. Workflow commit `3b692c81fadd98a2a45ec5c5a1c028aba903aeba`, automatically executed.
- GitHub run `37887100118` at https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37887100118 ; completed **SUCCESS** Oct9 05:08:23Z. Its meaning is SOURCE GATEWAY success, NOT a trading profitability or executability result.
- Artifact `11596816918`, name `mexc-convex-v01-causal-gateway-2026-10-09`, ZIP SHA256 `cfda65e51cad7060220e13dbf54e37cd8c6e1658dfe249e353d2c00938aafe25`. Immutable one-shot observation receipt, NOT append-only capital/trade state.
- Synthetic causal/quote/candle invariants PASS; Python syntax PASS.
- Live MEXC source calls use `/api/v1/contract/ping`, `/api/v1/contract/detail`, `/api/v1/contract/kline/<symbol>?interval=Min60`, `/api/v1/contract/depth/<symbol>?limit=20` public GET only. Four fixed BTC/ETH/SOL/BNB USDT perpetuals; 400 complete/contiguous 1H candles for hypothesis computation; 25/50/100 USDT synthetic reference sizes. No Binance fallback, private endpoint or exchange mutation.

## Actual observed source results
| Symbol | Public 1H + book source | Last book age at receipt | Spread (bps, single timestamp) | Candidate signal calculated off recent candle | Scorable after freeze? |
|---|---|---:|---:|---|---|
| BTC_USDT | PASS | 515 ms | 0.0121574561 | False, DESCRIPTIVE ONLY | NO |
| ETH_USDT | PASS | 1384 ms | 0.0402027020 | False, DESCRIPTIVE ONLY | NO |
| SOL_USDT | PASS | 957 ms | 0.9083064626 | False, DESCRIPTIVE ONLY | NO |
| BNB_USDT | PASS | 313 ms | 1.3468920466 | False, DESCRIPTIVE ONLY | NO |

Source blockers 0; all four passed the new SOURCE-only 25/50/100 reference size criteria. The earlier Oct9 MEXC source-only all-size $10/$25/$50/$100 gate remains **FAILED** because ETH/SOL $10 failed: this new separately preregistered source gate does NOT retroactively change that result or grant economic credit.

**Critical no-backfill boundary:** workflow commit occurred after the latest 05:00Z 1H candle close, so that candle was PRE-activation. The engine correctly stamped all four `NOT_SCORABLE_BOUNDARY`; zero creditable new forward signals, including no-signal events. This is GOOD governance and NOT an edge or trading signal result. First possible strict post-deployment hourly close is the first UTC hour boundary strictly after the new commit timestamp; only an on-time workflow execution within <=10 minutes of that boundary could ever count. This workflow is ONE SHOT, NOT scheduled recurring.

## What SOURCE PASS DOES NOT prove
- No actual prospective profitable signal or completed trade was observed, no capital position opened, no outcome scored.
- Quote freshness and 20 levels do not prove an order could fill; brokerage access restrictions, real account tier, actual taker fee, market impact, order size restrictions, funding and gap risk remain unverified.
- V5 frozen Parent 1H entry is reused as an exploratory candidate on MEXC; positive old Binance ETH/SOL/BNB history is not a valid MEXC replication. Parent V0.2 newest 3 losing resolved trades remain intact.
- Current script has only **one-shot artifact persistence**; it is not a durable single-writer trade ledger, order model or hourly collection schedule. Therefore NO performance/forward readiness GO.
- 95% historical allocation and 4% hard stop are NOT declared safe for a small account, no leverage rescue.

## Adjudication
**SOURCE_AND_QUOTE_TRANSPORT: PASS in 4/4 fixed symbols on this single collection.**
**POST-FREEZE_TIMELY_SIGNAL_OBSERVATIONS: 0.** `NOT_SCORABLE_BOUNDARY` for all; no fake signals counted.
**EXECUTABLE_FILL_VALIDATION: NOT DEMONSTRATED.**
**STRATEGY_NET_PROFITABILITY: NOT TESTED.**
**LIVE GO: NO.** Scientific NO_EDGE on the MEXC candidate would be inappropriate without independently observed future signals, executable entries/exits, realistic fees/slip/funding, and adequate sample.

## Legitimate next engineering phase (not activated here)
Freeze and test a durable single-writer append-only observer with reliable schedule shortly after every UTC 1H close and 100% observable eligible-signal coverage. If a run is late, record MISSED_SLOT with no forward credit; no retroactive market fill. Bind actual bid/ask/depth after signal, size and risk limits, observable stop/trail exit semantics, public funding/economic cost source or operationally BLOCKED. No position/PnL shadow should be activated before that next freeze. Genuine market executable NET edge must be audited separately, with original negative cross-asset evidence preserved.
