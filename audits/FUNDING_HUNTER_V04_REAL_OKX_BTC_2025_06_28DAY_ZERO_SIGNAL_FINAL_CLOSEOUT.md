# CRYPTO LAB — FUNDING HUNTER V04 — REAL JUNE 2025 BTC FUNDING RATE-ONLY CLOSEOUT

**UTC 2026-10-19 · FINAL pilot verdict: `NO_TRADE_UNDER_PREDECLARED_RULES` (28/28 dates FLAT). No economic edge or actual execution demonstrated. Not general economic NO-GO for all markets/dates.**

## Canonical real source evidence

- Preregistration **before market funding-rate outcomes**: `research/funding_hunter_v04/PRE_JUNE_2025_FUNDING_RATE_OUTCOME_FREEZE_2026_10_19.md`, commit `c04df25b`.
- Actual original OKX official June-2025 monthly ZIP archives: **BTC-USDT-SWAP linear** and **BTC-USD-SWAP inverse**, full schema `instrument_name,funding_rate,funding_time`. Accessed via official unsigned OKX 2025 month catalogue and two `static.okx.com` archive GETs in [GitHub Actions #39242521078](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39242521078), status SUCCESS.
- **90 valid chronological settled funding records per instrument**, original interval **8h throughout**, exactly 89 adjacent intervals per archive. First source UTC `2025-05-31T16:00:00Z`, last `2025-06-30T08:00:00Z`. Original publisher month groups on a **UTC+08** calendar boundary, not the strict June UTC month.
- The initial source attempt **correctly failed closed** before opening funding rates: [run #39242064119](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39242064119) identified out-of-UTC-month timestamp `2025-05-31T16:00:00Z` (Jun 1 00:00 UTC+8). Scientific source-only amendment `V04B_PRE_OUTCOME_UTC8_ARCHIVE_MEMBERSHIP_SCHEMA_AMENDMENT.md` commit `003483dc` froze exactly `2025-05-31T16:00:00Z <= settlement < 2025-06-30T16:00:00Z`, BEFORE opening any numeric funding rate. **No change** to entry hours, 28 days, prior rate threshold, 24h hold, cost benchmarks or sign logic. Unexpected UTC/interval/duplicate/new year still fails.
- Windows and Linux **19/19 hermetic tests PASS EACH** in run #39242521078, followed by real source read PASS. SHA256 of both official ZIPs, decompressed member and timestamps captured in a sanitized GitHub Actions artifact; raw archives **never committed**.
- Independent read-only reconciliation of original persisted receipt: [GitHub Actions #39242841001](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39242841001), SUCCESS, no new exchange calls, confirms full 28/28 original days and source metadata.

## Fixed preregistered decision and observed results

- Daily original UTC 00:05 entry times for **June 2 through June 29** 2025: exactly **28** frozen candidate 24h periods. Last settled funding for both contracts strictly precedes each entry, using the preceding pair of settlements and real 8h periods; no lookahead.
- Rate-direction variable: `linear_lagged_rate_bps_per_hour - inverse_lagged_rate_bps_per_hour`; require **absolute >=0.5 bps/hour**. Positive -> short linear / long inverse; negative -> short inverse / long linear; below threshold -> FLAT.
- **All 28 times FLAT**; 0 qualifying position decisions, 0 conditional rate-only cashflow episodes, 0 opened orders, 0 real fills, 0 funding payouts from this frozen system. The rate-only proxy totals of **0 USD** are strictly **because it would have taken ZERO positions**, not a trading PnL track record.
- Actual maximum observed absolute lagged differential **0.153790283363375 bps/hour**, just **30.76%** of the frozen 0.5 threshold. Signed observed lagged extremes: **-0.153790283363375 to +0.105842141218125 bps/hour**.
- Merely **extrapolating** the maximum lagged spread unchanged for 24h => **3.690966800721 bps** on one fixed-notional basis, **NOT realized forward funding**, not mark-valued historical settlement, not assured cash inflow or net PnL.
- Original V01 +30/+50bps round-trip per-one-leg notional benchmarks were merely planned **MEXC/Binance scenario costs**. They are NOT OKX historical/account fee measurements and were not applied to any executed/simulated V04 position (none). We must not declare venue economics dead based on them, or reduce fees postoutcome to create signals.

## Formal scientific consequences

`V04_BTC_JUNE2025_FIXED_RULE_NO_TRADE` is a defensible TRUE historical screened-decision verdict, **not** `PROFITABLE`, `ECONOMIC_NO_GO_FOR_ALL_MARKETS`, `NO_FUNDING_EDGE_EXISTS`, or an account-recognized PnL. Historical sample and two 2025 L2 books have already been inspected in earlier V03; **zero OOS credit**.

The V04 source gate for monthly funding rate/timestamps is no longer blocked, but a full economic test would still lack 2025 source-certified paired **exact settlement mark**, historical inverse `ctVal`/`lotSz`/`tickSz`, independent collateral BTC/USD-USDT FX, funding cashflows denominated in correct currency, all 24h **future exit** bid/asks, filled quotes and real fee schedule. Two existing June-2 books are source quote evidence only, not traded 24h episodes.

**Action**: STOP acquiring costly raw full 2025 BTC 400L2 exit books for this exact frozen June 2–29 signal configuration. Do not lower 0.5bps/hour to salvage a favorable in-sample episode, do not choose an asset/timeframe based on seeing results. Close this one-month pilot now. Other economically distinct mechanisms, genuine forward signal/settlement data or a newly pre-outcome frozen independent test may be legitimate, but no current strategy is promoted.

No live trader/stop/API key/account/money/Render/Windows intervention; no 2026 market holdout accessed; main unchanged. PR draft only. **Final money-machine claim: NO, NOT DEMONSTRATED.**
