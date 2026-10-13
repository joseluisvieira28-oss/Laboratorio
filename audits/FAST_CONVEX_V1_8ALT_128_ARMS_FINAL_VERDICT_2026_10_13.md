# FAST-CONVEX V1 — 8 ALTCOINS × 4 FAST TF × 2 HOLD CAPS × 2 COST ARMS
**Closeout 2026-10-13 UTC. Status: HISTORICAL_FAST_FAIL / NO ACTIVE EDGE / NO TRADING AUTHORITY.**
Frozen *before performance* in `research/fast_convex_8alt_v01/PREOUTCOME_FAST_EXIT_FREEZE_2026-10-13.md` commit `6e115c2d2f83010e5699af9afaf6aebe4f1881a9`.
Reference original core Parent V5 source V1/V2 and frozen prior common 2023-25 8-alt V5 OHLCV market calendar, left unchanged. No main merge, protected 2026 holdout opened, private exchange account/wallet/order, Render or real trading.
**Primary immutable 128-arm source execution:** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38446416504 — SUCCESS: 9 synthetic causal/cost/timehold tests pass; **8/8 symbols completed** their full 16-arm historical simulation, all complete parent official Binance Vision 5m + independent 1h + funding source ZIP checksums.
**Audited immutable 128-cell master:** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38447186832 — SUCCESS: all original source trade ledgers/master SHA receipts, 128-result JSON and CSV artifact https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38447186832/artifacts/11839655591 . Earlier master attempts failed for administrative reasons (original run still in progress, then original aggregator accidentally compared CSV filename stems including `_TRADES` suffix with bare arm keys). These are master aggregation errors, **not economic strategy outcomes**; corrected master is in independent `research/fast_convex_master_final_20261013/master.py` and source 128-arm run was not modified post-outcome.
Verification: per source symbol 333216 continuous officially ZIP-SHA256-verified 5m market bars and 27768 official 1h bars (including warmup Nov/Dec 2022), 3288 archived funding events. Independent published official 1h market archive differs in 4–5 bars per symbol versus canonical 5m aggregation, **zero 1h V5 entry signal mismatches** over compared economic years; source equivalence not falsely asserted.

## Why this is a distinct experiment, no falsified independent OOS
User requested frequent operations rather than multi-day/month signals and >30d wait. A separate V1 strategy family explicitly **changed the exit mechanism before viewing its FAST outcomes**:
- ETH BNB SOL XRP DOGE ADA LINK AVAX (eight frozen alts), 5m, 15m, 30m, 1h original V5 RSI/BB/SMA200 confirmed bar *LONG-only* entry (20% portfolio paper notional), entry 5m open strictly AFTER signal was witnessed.
- Entire common 2023–25 full market and funding archive, no selective regime/year truncation or missing months; Nov/Dec 2022 source warmup; 2026 untouched.
- FAST8H primary and FAST24H sensitivity: fixed +1.2% take profit, -0.6% stop, forced close at bar OPEN after 8h or 24h, intrabar stop-first; gaps at observed open. One active slot, no leverage. 8bps assumed taker fee **each side** plus BASE adverse 2bps/side or STRESS 5bps/side, public Binance USD-M archived funding rates × 5m market OPEN (not verified settlement mark). Account 10,000 USDT independently simulated for every coin/TF/cap/cost; trade ledgers include open end positions, cashflow residuals, annual series, fees/funding/MTM downside. No actual order book fills or MEXC specific funding.
- Frozen 6 strict descriptive gates: BOTH BASE/STRESS net>0 and PF>1.15, at least 52 closed trades **each** 2023/2024/2025, 3/3 positive net closed-PnL years, DD >=-20%, CAGR >=10% model, and positive static closed ledger PnL after subtracting top3 winners. Passing historical gates still only qualifies for untouched future OOS research.

## NUMBERS — all 128 historical trading models on unchanged original price years
**128/128 VALID source+model cells; 0/128 positive NET terminal marked returns; 0/64 symbol×TF×hold groups pass strict gates. ALL four timeframes, both hold caps, both cost scenarios negative on every asset.**
Best BASE case from each asset (selected just to show complete failures; do not optimize trading parameters by picking this):
| Asset | Least negative frozen FAST arm | Closed trades 2023–25 | Trades/wk | Profit Factor BASE | 3y NET marked % |
|---|---|---:|---:|---:|---:|
| ADAUSDT | 1h FAST24H | 264 | 1.686 | 0.734 | **-6.723%** |
| XRPUSDT | 1h FAST24H | 256 | 1.635 | 0.704 | -7.403% |
| BNBUSDT | 1h FAST8H | 273 | 1.744 | 0.621 | -9.279% |
| SOLUSDT | 1h FAST24H | 302 | 1.929 | 0.636 | -10.843% |
| AVAXUSDT | 1h FAST8H | 288 | 1.839 | 0.586 | -11.638% |
| ETHUSDT | 1h FAST8H | 313 | 1.999 | 0.593 | -11.679% |
| LINKUSDT | 1h FAST24H | 278 | 1.776 | 0.545 | -12.725% |
| DOGEUSDT | 1h FAST8H | 283 | 1.807 | 0.522 | -13.543% |
The best by return was **ADA 1h FAST24H** with **-6.723% BASE / -9.474% STRESS**, PF 0.734/0.644, zero positive exit years, static top3-removed negative; NOT an economic survivor.

## The false goal: more trades ≠ better trading economics
Among fastest observed arms, **SOLUSDT 5m FAST8H** achieved **2011 closed trades across 3 years ≈12.844/week** on already-known market history and losses of **-48.162% BASE**, **-60.035% STRESS**, PF 0.672 BASE, modeled DD -48.344%; 2023/2024/2025 annual trades 667/678/666, yet zero positive closed-PnL calendar years. FAST24H SOL5m still ~2007 trades and ~-48.87% BASE.
Likewise AVAX 5m FAST8H 1933 trades ~12.35/week returned -56.29% BASE; DOGE 5m FAST8H 1875 trades ~11.98/week returned -54.92%. Churning frequent small positions compounds fees and expectancy losses, **not income**.
Simplified frozen fee+slip roundtrip alone is **20bps BASE** or **26bps STRESS** of traded notional, before bid/ask spread, funding, actual impact and stop gaps. For idealized target +1.2% / stop -0.6% and zero timeouts, win fractions would have to exceed ~44% just to break even BASE. Actual exits also include timeouts/gaps/funding; this simple hurdle is illustrative, not an actual complete PnL proof.
We did NOT retro-optimize TP, SL, V5 entry filters or 8h/24h after seeing loss outcomes. We did NOT convert a FAILED NET model to approved maker execution or zero fees. Past BTC V5 5m scalp also failed historically: this independent alt/TF fast study likewise lacks a net mechanism.

## Scientific verdict and allocation
- **FAST-CONVEX V1 2023-25 = REJECT / DEPRIORITIZE EXACT 1.2% TP, -0.6% STOP, 8/24H with original V5 long entry across eight alts/5m/15m/30m/1h.**
- No live candidate, no micro-live, no additional forward monitor for this failed fast family, no parameter salvage on seen outcomes; original SOL1h/BNB4h slow 2023-25 descriptive results remain a distinct study and are not retroactively killed by these different exits, but are too infrequent to meet the user's short-term income goals.
- To explore fast trades economically, seek a **different independently motivated mechanism**, not another take-profit sweep on same data. Candidate source-first hypotheses might include venue-specific measurable funding/forced-flow/spread dislocations **IF** sourced contemporaneously and economically before outcomes; avoid unbacked "frequent win" extrapolation. Alternative lower fee maker routes require verifiable fill rates, queue position, actual user fees, minimum contract/lot and adverse selection, not optimistic 0bps assumptions.
- All proof is historical **already-studied price years** and not untouched OOS, with Binance market 5m proxy not a real MEXC future execution. No 30-day wait needed to falsify this candidate; real profit guarantee or independent forward verification cannot be shortcut merely by trading more frequently.
**FINAL: ALL 128 NET NEGATIVE / 0 SCIENTIFIC CANDIDATES / SOURCE AND SYNTHETIC GATES SUCCESS / TRADING_AUTHORITY NONE.**
