# MVE-SIMPLE4H-01 — PROSPECTIVE 2025 REPLICATION FREEZE — V0.2

Date: 2026-09-17
Status: PROMOTION_GATE_PREP / 2025 STILL LOCKED
Repository: joseluisvieira28-oss/Laboratorio
Research only. Fail closed. No live trading, no exchange mutation, no 2026 access.

## 1. Identity and historical verdict
This is a NEW MVE replication hypothesis derived from SIMPLE TRADING LAB V0.1.
The historical 2021-2024 verdict is immutable: 36/36 primary cells complete; 27 NEGATIVE_EXPECTANCY; 9 NO_STATISTICAL_EDGE; 0 SURVIVES_DISCOVERY.
The seven cells below are historical positive diagnostics only. They are not retroactive survivors.

MVE family ID: MVE-SIMPLE4H-01
Replication cohort: all seven cells jointly frozen.

### Fixed seven cells
1. ST-01_DONCHIAN_BREAKOUT — BNBUSDT — 4H
2. ST-01_DONCHIAN_BREAKOUT — DOGEUSDT — 4H
3. ST-01_DONCHIAN_BREAKOUT — SOLUSDT — 4H
4. ST-01_DONCHIAN_BREAKOUT — XRPUSDT — 4H
5. ST-02_EMA_PULLBACK — SOLUSDT — 4H
6. ST-02_EMA_PULLBACK — DOGEUSDT — 4H
7. ST-03_EXTREME_MEAN_REVERSION — DOGEUSDT — 4H

No cell may be added, removed, substituted, or parameter-adjusted after 2025 outcome access.

## 2. Recovered source authority
Recovered original package ZIP SHA256:
2bd1fa5170f2464445164caa7cf5f8b9df4808464cbd3aef30978f445771873e

Internal authority hashes:
- SIMPLE_TRADING_LAB_SCIENTIFIC_FREEZE_V0.1.md = 6f126041a8729f6ecec89afb92c4b58a5f391f91f00b855f5cd1becdbc1a8efa
- simple_trading_lab_v01.py = b4549b53247ff67c8bf4cbbf780611c8231eb1be72a52ae240168de2fa7ac71a
- README_WINDOWS.txt = 7221551e75bf4a5c5f28d78953a9b17f8a628a3939287d28ce8e36af1ad8b57a
- requirements.txt = be039e3cc3af78324d429337251146670ded768c1bac2ed479fe77ecf25fc63c

Recovered results ZIP SHA256:
b23798fbe6b8f674be94014add8d2b00278cffdcf7889a01b2ec0917fd89134d

Results authority hashes:
- ST_CLOSEOUT_V0.1.json = 6e08f5ca8b9578e551cab31a70b6b8c8ae6e3ab33e766691dbc31851f15062b2
- ST_EVENTS_V0.1.csv.gz = dc33df026d851cf4e7245b33c7b842e164b70ba783d38cef6d606b57b46a3f11
- ST_PRIMARY_36_CELL_SUMMARY_V0.1.csv = 5e9873d830d8f08d754be2c2b507c3c5631242a9043643ad9f9ce3bf0d349f0f

Recovered machine-readable ledger: 32,243 completed events.
Basic recomputation of N, NET10 mean, NET14 mean and NET10 win rate against the 36-cell summary: 36/36 PASS.

## 3. Inherited economic rules — byte-grounded
All rules below are inherited exactly from the recovered V0.1 authority.

### Indicators
- EMA20: ewm(span=20, adjust=False) on completed closes.
- EMA50: ewm(span=50, adjust=False) on completed closes.
- ATR14: Wilder-style TR ewm(alpha=1/14, adjust=False).
- Donchian levels use previous 20 completed bars, excluding the signal bar.

### Entry
- Signal evaluated on completed bar i.
- Entry at exact OPEN of bar i+1.
- No same-bar entry.
- One active position per cell; signals while position is active are ignored.

### Intrabar convention
- Gap through stop: exit at bar open; adverse gap honored.
- Gap beyond target: exit at frozen target; no favorable gap improvement.
- If stop and target are both touched and sequence is unknown: STOP first.

### ST-01 Donchian Breakout
- Long: close_i > previous-20-bar high.
- Short: close_i < previous-20-bar low.
- Stop: 2.0 x ATR14 from entry.
- Target: 4R.
- Max holding: 20 complete bars after entry; otherwise exit at the next bar OPEN.
- No trend filter.

### ST-02 EMA Pullback
- Long: EMA20 > EMA50; low <= EMA20; close > EMA20; close > open.
- Short: EMA20 < EMA50; high >= EMA20; close < EMA20; close < open.
- Stop: 1.5 x ATR14 from entry.
- Target: 2R.
- Max holding: 10 complete bars.

### ST-03 Extreme Mean Reversion
- Long: close < EMA20 - 2.0 x ATR14.
- Short: close > EMA20 + 2.0 x ATR14.
- Stop: 1.5 x ATR14 from entry.
- Target: EMA20 frozen at signal bar.
- Invalid if next-bar entry has already crossed beyond frozen target.
- Max holding: 8 complete bars.

### Costs
- BASE: 10 bps round trip once per completed trade.
- STRESS: 14 bps round trip once per completed trade.
- No maker rebates.
- Cost reduction is forbidden.

## 4. Data and temporal firewall
Historical Discovery already exposed: 2021-01-01 <= signal < 2025-01-01.
Protected confirmation cohort: 2025-01-01 <= signal < 2026-01-01.
2026 remains LOCKED.

Replication market/source must remain Binance USD-M Futures 1m, same product class as the parent lab.
4H bars require exactly 240 native 1m observations; no interpolation or forward fill.
A 2024 warm-up tail may be used solely to seed EMA/ATR/Donchian state before the first eligible 2025 signal. No 2024 signal may enter the confirmation sample.
The confirmation cohort starts FLAT at 2025-01-01T00:00:00Z: positions triggered by pre-2025 signals are not inherited into the holdout. This boundary-state rule is frozen before 2025 access.
Official source contract: Binance public-data USD-M Futures monthly 1m kline ZIPs and their adjacent `.CHECKSUM` sidecars for 2024-12 warm-up plus 2025-01 through 2025-12 for the four required assets (BNBUSDT, DOGEUSDT, SOLUSDT, XRPUSDT).

### End-of-2025 censoring rule
No trade may require a 2026 bar for adjudication.
Signals too near the end of 2025 to guarantee their maximum holding horizon plus deterministic time-exit inside 2025 are excluded BEFORE checking whether stop/target would have occurred early. This prevents outcome-dependent censoring and preserves the 2026 firewall.

No 2026 file may be downloaded, read, listed for outcome purposes, or used as an exit bar.

## 5. Prospective 2025 statistical family
The new replication multiplicity family is exactly the seven fixed cells above.
Historical q-values from the original 12-cell strategy families are context only and are not reused as 2025 decision values.

For each 2025 cell report:
- N completed trades
- gross mean/median
- NET10 mean/median
- NET14 mean
- NET10 win rate
- SD / SE
- Student-t 95% CI for NET10
- one-sided t-test H1: mean NET10 > 0
- max drawdown on cumulative NET10 log returns
- mean R multiple
- stop / target / time-exit frequencies
- calendar-quarter NET10 means
- top-trade and top-quarter profit concentration diagnostics

BH-FDR: 5% across the seven frozen 2025 cell p-values.
Bootstrap: circular moving-block bootstrap, 3000 reps, block length 5 trades, deterministic cell-specific seed derived from the frozen seed text `MVE_SIMPLE4H_01_2025_V01`.

## 6. Sample and promotion gates
### Sample adequacy
- N >= 100: promotion-eligible sample.
- 50 <= N < 100: diagnostic-only / may support TIER_3 but cannot by itself support TIER_2 or QUASE_DIAMANTE.
- N < 50: INSUFFICIENT_SAMPLE for that cell.

The N>=100 promotion floor is inherited from the parent lab and is NOT lowered to rescue the one-year holdout.

### STRONG_CELL_PASS
A cell is STRONG_CELL_PASS only if all are true:
1. N >= 100
2. NET10 mean > 0
3. NET14 mean > 0
4. BH-FDR q across seven < 0.05
5. moving-block-bootstrap lower 95% NET10 mean > 0
6. positive NET10 mean in at least 3 of 4 calendar quarters

### Concentration red flags
For any otherwise-passing cell:
- largest single winning trade > 25% of total positive NET10 bps => concentration red flag
- largest positive quarter > 60% of total positive NET10 bps => temporal concentration red flag
A concentration red flag blocks QUASE_DIAMANTE promotion and routes at most to TIER_3 pending further evidence.

### Family routing
- TIER_2 / PROMOTED_CANDIDATE: at least 2 STRONG_CELL_PASS cells spanning at least 2 distinct strategy families, family median NET14 > 0, and no concentration red flag on promoted cells.
- TIER_3_WATCHLIST: exactly 1 STRONG_CELL_PASS OR at least 4 of 7 cells with N>=50 and positive NET14, provided the family does not meet TIER_2.
- REJECTED / STONE: zero STRONG_CELL_PASS, at least 5 of 7 cells with N>=100, and median NET14 <= 0.
- NO_EDGE: zero STRONG_CELL_PASS, at least 5 of 7 cells with N>=100, but the REJECTED condition above is not met.
- INSUFFICIENT_SAMPLE: fewer than 5 of 7 cells reach N>=100 and neither TIER_2 nor TIER_3 criteria are met.

QUASE_DIAMANTE is not automatic from this freeze. It requires TIER_2 plus clean provenance, realistic costs, no fatal concentration, and human scientific review confirming that the 2025 sample is a valid independent OOS confirmation.

## 7. Expected sample before holdout opening
For planning only, using parent Discovery counts divided by four years gives rough annual counts:
- Donchian BNB: ~75
- Donchian DOGE: ~69
- Donchian SOL: ~76
- Donchian XRP: ~68
- EMA SOL: ~107
- EMA DOGE: ~112
- Extreme MR DOGE: ~77
These estimates are NOT 2025 outcomes and cannot be used to alter the gates above.

## 8. Forbidden after freeze
- no parameter sweep
- no new assets
- no 1H cells
- no cell dropping
- no alternate costs below 10 bps
- no stop/target/timeout change
- no regime filter
- no indicator stacking
- no post-outcome threshold changes
- no 2026 access
- no live trading or exchange mutation

## 9. Promotion-gate state
The source-rule blocker is resolved.
This document does NOT authorize opening 2025 data.
Required before one-shot 2025 run:
1. authority/preflight receipt PASS on recovered package/results hashes;
2. implementation tests PASS without protected data;
3. exact branch HEAD frozen;
4. explicit protected-data authorization for 2025 only.

Until all four are true: FAIL CLOSED.
