# CRYPTO LAB — BTC CONVEX: VENUE HISTORICAL EXECUTION, FUNDING, QUOTE AND CAPITAL FEASIBILITY CLOSEOUT
Date 2026-10-09 | Mode research-only, no trading, no private endpoints, no main merge, 2026 outcomes sealed
Branch `research/convex-venue-execution-source-gate-2026-10-09`

## Adjudication
**HISTORICAL ORIGINAL BINANCE SCIENCE: SCOPE-LIMITED PASS** in original first ETH/SOL/BNB basket (2021–2025), unchanged. Previous 13-asset expansion and global fail unchanged.
**REAL-WORLD MEXC 2021–2025 COMPLETE EXECUTABLE AFTER-ALL-COSTS NET EDGE: NOT PROVEN.** Source blockers are precise, not a strategy "NO_EDGE" or definitive death:
- Target venue original 2021–2025 **point-in-time BBO/depth archive: SOURCE_NOT_ESTABLISHED**. MEXC public depth endpoint returns CURRENT quotes and contract metadata only, cannot backfill original quote fills.
- Target MEXC **official funding history before 2025-04-17 16:00 UTC is not present in the queried public history**. Three target instruments' earliest returned history was 2025-04-17 in the 2026-10-09 scan; no right to substitute Binance historic funding as identical MEXC funding.
- Native MEXC **2021–2025 official 1h OHLCV**: sampled dates each passed, but full census found **16 missing 1h observations across 183 monthly requests**. Same exchange official `Min1` public query recovered **0/16 complete missing hours**; nearest preceding controls failed too. FULL MEXC NATIVE PRICE-ONLY replay was correctly **FAIL_CLOSED BEFORE STRATEGY OUTCOMES**, so there are NO new MEXC five-year returns, not even funding-excluded.
- Our current MEXC contract minimum notional and fee viability gate is only a snapshot; a mathematical sizing PASS cannot prove order acceptance or funded execution.

Therefore:
`BINANCE_HISTORICAL_LOCAL_PASS` (scope-limited) / `BINANCE_13_ASSET_GENERALIZATION_FAIL` / `MEXC_SOURCE_COVERAGE_BLOCKED` / `MEXC_HISTORICAL_BBO_UNVERIFIED` / `MEXC_FUNDING_2021_2025_INCOMPLETE` / `REAL_EXECUTABLE_NET_EDGE_UNVERIFIED` / `LIVE_GO_NO`.
Historical science no longer waits for future events, but missing venue data cannot be waived to award an executable-net PASS.

## Canonical new source/feasibility experiments and receipts

### (A) MEXC public 2026-10-09 depth/contract and 2021–2025 historical funding gate
Run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37919451421 — SUCCESS, artifact 11611039148.
- Actual public contract/depth access ETH_USDT/SOL_USDT/BNB_USDT PASS CURRENT ONLY. API fields contractSize, minVol, volUnit, apiAllowed, book BBO time and size are visibly recorded; no authenticated exchange reads.
- The public `/api/v1/contract/funding_rate/history` returned 1620 records per contract over 2 pages; oldest returned `2025-04-17T16:00:00Z`. Inadequate for all 2021–2025.
- Official `/api/v1/contract/depth/{symbol}` has current snapshot timestamp; official `depth_commits` provides **last N**, not a dated 2021–2025 archive.
- Original Binance model assumed commission 10bps SIDE and adverse fixed BASE slip 2bps SIDE, STRESS slip 5bps SIDE, plus historic *Binance* funding, not MEXC.
- MEXC official API Futures fee bulletin published May 28, effective June 1 2026 08:00 UTC, maker 6bps SIDE, taker 8bps SIDE (=16bps taker-taker fee ONLY). Raw public contract detail fields from this scan paradoxically showed makerFeeRate 0 and takerFeeRate 0.0002; **do not use lower raw metadata fees to override official stated API fee schedule absent account-specific binding proof**, and do not infer Swiss user regional access. Fee bulletin https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742 .

### (B) Official Binance historical bookTicker BBO archives (different venue)
V01 historical HEAD inventory tests of five dates per original symbol: 2021-01-02, 2023-05-24, 2024-01-15, 2025-06-17, 2025-12-01. Archive availability established for **2023-05-24 and 2024-01-15** for all three; not established for the other probed days. This does not prove no other archives exist.
V02 real ZIP/PAYLOAD verification run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37919685828 — SUCCESS, artifact 11611356244:
- BNBUSDT 2023-05-24 official ZIP sha checked PASS; first 1000 BBO lines valid, **median sample spread 0.319005bps**;
- SOLUSDT 2023-05-24 ZIP SHA checked PASS, 1000 valid, median **0.499164bps**;
- BNBUSDT 2024-01-15 ZIP SHA checked PASS, 1000 valid, median **0.333572bps**.
- ETH 2023 and 2024 and SOL 2024 archives were **source bytes size above pre-frozen 80MB per archive**, NOT data corrupt nor genuinely unavailable.
- These first-1000-row source/schema samples are NOT original trade T0 quotes and NOT overall market time-weighted spreads; no inference to 2021–2025 economics, no conversion into MEXC BBO, no paid data.

### (C) Public contract minimum notional and risk per trade
Run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37919959640 — SUCCESS, artifact 11611735192.
Frozen two planned per-trade risk levels .25% or .50% and original 4.24% notional planned stop+cost loss denominator (not guaranteed max loss); account examples 100/250/1000/10000 USDT, **hypothetical**, no real account read.
As seen in the 2026-10-09 public snapshot, contractSize*minVol*best_ask:
| Symbol | Approx single minimum contract notional | Approx equity needed at .25% planned per-position risk |
|---|---:|---:|
| ETH_USDT | 24.9206 USDT | 422.653376 USDT |
| SOL_USDT | 10.96 USDT | 185.8816 USDT |
| BNB_USDT | 7.426 USDT | 125.94496 USDT |
For hypothetical 100 USDT and .25% risk all 3 are `NOT_TRADABLE_UNDER_PLANNED_RISK`. 250 USDT permits one minimum BNB or SOL model contract but not ETH; 1000 USDT permits all 3 (order acceptance, exact available depth/capacity/region not established). Sizing rounds **down** only to contract volume unit; no risk violation to force minimum volume. Date/quote sensitivity explicit.

### (D) Native MEXC original-market hourly historical price history
A source-only fixed nine-day probe run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37920213085 — SUCCESS, artifact 11610339986; exact 24/24 hourly bars for 2021-06-15, 2023-06-15 and 2025-06-15, each of original ETH SOL BNB (9/9).
Separate **original Parent price-only source freeze** `PRE_MEXC_NATIVE_5Y_PRICE_TRANSFER_FREEZE_V01.md` required exact 61 months and 100% 1h bars 2020-12 warmup through 2025-12; same originally pinned Parent signal, 10bps original fee, 2/5bps slip and 0.25/0.5% shared portfolio, explicitly MEXC funding unavailable.
- First workflow 37920627684 failed Python compilation BEFORE source retrieval; correction documented `TECHNICAL_SYNTAX_REPAIR_BEFORE_REPLAY.md` and only structural indentation fixed, no scientific change.
- Corrected workflow https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37920812103 downloaded official MEXC source through 2021 Sep; FAIL_CLOSED with `MONTHLY_MEXC_SOURCE_HOLES:SOLUSDT:2021-10:742:744`; no strategy/economic output was executed.
- Independent new purely SOURCE-ONLY freeze `PRE_MEXC_OFFICIAL_MIN1_GAPFILL_CENSUS_FREEZE_V01.md`, then workflow https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37921127878 — SUCCESS as **source classification**, artifact **11611627557**.
- All 183 monthly REST returns obtained and checked across full frozen 2020-12 through 2025-12 scope. Source inventory found exactly **16 missing 1h timestamps**, plus the origin metadata: 
  - 2021-10: ETH 2 / SOL 2 / BNB 2
  - 2022-01: ETH 3 / SOL 3 / BNB 3
  - 2023-08: BNB 1
- For these precise 16 missing 1h timestamps, same-source public MEXC `Min1` exact 60-minute reconstruction checked and **0/16 qualified**. Controls of nearest existing earlier 1h via `Min1` also unavailable; hence no source-safe substitute.
- FAIL-CLOSED `SOURCE_COVERAGE_BLOCKED` under predeclared all-hours coverage requirement, **not a negative economic backtest**. Historical exchange-wide gaps may be possible but their causes not proved; never insert candle from Binance, forward fill, interpolate, shift date ranges or silently drop missing hours.
- Original fixed Binance historical PASS and 13-asset generalization FAIL remain unchanged; this is MEXC source feasibility, no new independent held-out price outcomes.

## Next scientifically legitimate high-value steps
1. **Do not execute live money** or build funded auto-trader now. A source gate CI success (the final one) was a SUCCESS in finding a definitive SOURCE BLOCKER, **NOT a success of PnL**.
2. If exact native MEXC historical execution is necessary, seek a **documented, affordable archived MEXC Futures 2021-2025 order book BBO+depth AND complete native funding**. Obtain official evidence to explain/outsource exchange-missing 16 hours. Without these three, do not use historical source transfer to promote LIVE_GO.
3. A *distinct* economically legitimate venue-selection study may instead preserve the original signal and evaluate an exchange with provable full historic quotes, actual fee tier and funding coverage with predetermined new source windows and constraints, without post-outcome retuning. Native Binance bookTicker 2023/24 sample alone is insufficient, and venue status must be checked for locale, contracts and automation restrictions.
4. **Why the previous result mattered**: original Binance 0.25% planned risk shared first basket +34.59609% five-year simulated cumulative with hourly-close marked DD -8.6650%, first-run raw-and-funding reproduction run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37916963862, 1m stop-first-touch run 37917719450. These are archived source + bar-model rule results, not realized exchange quotes and no guaranteed future income.
5. Clearly separate `HISTORICAL_LOCAL_PASS` / `EXECUTION_SOURCE_BLOCKED` / `NO_EDGE`; do not declare hard NO_EDGE from missing execution data.

No merge, no live trades, no account, no private API or wallets, no trading signals/outcome manipulation, no opening 2026 protected OOS, no paid data.
