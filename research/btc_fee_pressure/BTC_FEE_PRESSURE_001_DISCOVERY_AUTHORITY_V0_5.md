# BTC-FEE-PRESSURE-001 — DISCOVERY AUTHORITY V0.5

MVE_ID: BFP-TOTALFEES-7D-001  
DATE_FROZEN: 2026-09-14 UTC  
STATUS: FROZEN PRE-OUTCOME / ONE-SHOT DISCOVERY AUTHORIZED  
DRIVE AUTHORITY: 1zKdIasUa8ask7R_vlbf-3TBsDSC1x4EeyH6r9oMWRZE  
BRANCH: btc-fee-pressure-v0.5-discovery

## Governance
Research-only, fail-closed. No live trading, exchange mutation, main merge, Render deployment, post-outcome tuning, cherry-picking, or 2025/2026 access. This authority opens only 2021-2024 Discovery outcomes.

## Canonical source binding
V0.4 source gate verdict: SOURCE_DATA_PASS. Run 34886378068; tested HEAD 945b57823fb91e767fd42c79ed2d362fce85d19f; artifact 10365390379; artifact ZIP SHA256 4d6b3a0a5738d8daf36b416a7e3ba83c5d8a647cf11eae734a0499a5edf2fca8; manifest SHA256 4af2e98ac18aaf28686f7f80580ece5a7a34461f20e1955ad562e0a7328c9093; Drive evidence 1f_iG_eYyYnLagjvchO-cUwpzm1N3JiPU. Coverage 1461/1461 UTC days, 2021-01-01 through 2024-12-31, zero missing days/heights and zero malformed rows.

## Immutable hypothesis
Daily total Bitcoin transaction fees paid to miners are treated as demand for scarce block space. Unusually high fee pressure is expected to precede positive future BTC return. Direction is LONG BTC only. No inversion, alternate metric, filter, threshold sweep, stop, take-profit, or redesign.

## Signal
For completed UTC source day t with exactly 90 complete prior observations, compute the trailing 80th percentile on t-90...t-1, excluding t. Percentile definition is Hyndman-Fan Type 7 / linear interpolation: with sorted x[0..n-1], h=(n-1)*0.80 and linear interpolation between floor(h) and ceil(h). Signal iff FEE_PRESSURE_t > P80_90(t), strictly; equality is no signal.

## Timing and overlap
Signal becomes available only after completed UTC day t. Entry = BTCUSDT daily OPEN 00:00 UTC on t+1. Exit = BTCUSDT daily OPEN 00:00 UTC on t+8. Hold = exactly 7 calendar days, interval [entry, exit). Candidate signals are processed chronologically and accepted only when entry >= previous accepted trade exit; otherwise suppressed. No extra publication delay is added because V0.1 froze next UTC daily open after signal.

## Discovery window
Source 2021-01-01..2024-12-31. Earliest signal is first day with 90 complete priors. Latest eligible signal 2024-12-23, making final entry 2024-12-24 and final exit 2024-12-31. Any 2025 timestamp is forbidden and must fail closed.

## Market outcome source
Official Binance Public Data / Data Vision SPOT **daily** BTCUSDT 1d archives only. Only exact entry/exit dates selected outcome-blind may be downloaded. Path family: https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-YYYY-MM-DD.zip plus matching .CHECKSUM. Dates limited to 2021-2024. Only open_time and open are outcome fields. Every ZIP must match official checksum. No alternate exchange/API fallback or stitched source.

## Outcome-blind selection freeze
Write and SHA256-hash the complete accepted signal/trade-date list before any market ZIP is downloaded. The outcome step must verify that hash before accessing market files. No price-dependent inclusion/exclusion.

## Return and costs
raw_return = exit_open / entry_open - 1; gross_bps = 10000 * raw_return. NET10 = gross_bps - 10 bps [PRIMARY]. NET20 = gross_bps - 20 bps [STRESS]. Costs once per accepted trade.

## Frozen statistics
Report N; candidate signal count; accepted/suppressed overlap counts; mean and median gross bps; mean NET10 and NET20; NET10 profit factor; NET10 win rate; per-calendar-year N and mean NET10, assigning each trade to `entry_day` year; bootstrap distribution of mean NET10 with seed 20260914 and 10,000 resamples; bootstrap p(mean NET10 <= 0); Type-7 95% bootstrap CI; maximum positive-year gross contribution share defined as max(positive annual gross-bps sum) / sum(all positive annual gross-bps sums); cumulative NET10 and max drawdown in chronological accepted-trade order as diagnostics. A year with zero accepted trades cannot count as a non-negative year for promotion.

## Promotion gates — all required
1. N >= 50 accepted non-overlapping trades.
2. Mean NET10 > 0 bps/trade.
3. NET10 profit factor > 1.00.
4. At least 3 of 4 calendar years 2021-2024 have non-negative mean NET10.
5. Bootstrap p(mean NET10 <= 0) <= 0.20.
6. Maximum positive-year gross contribution share <= 70%.
7. Source binding, selection hash, market checksum, timing/non-overlap and protected-period firewalls all PASS.
Median gross, NET20 and drawdown are diagnostics, not hidden rescue gates.

## Terminal states
DISCOVERY_PASS_CANDIDATE; DISCOVERY_FAIL_NO_PROMOTION; TECHNICAL_FAILURE_PREOUTCOME; TECHNICAL_FAILURE_POSTOUTCOME; DATA_FAILURE; PROVENANCE_FAILURE.

`TECHNICAL_FAILURE_POSTOUTCOME` is reserved for transport/infrastructure failure after market access has begun and must never be collapsed into DATA_FAILURE or NO_EDGE.

## No-rescue rule
If this exact MVE fails, do not invert it, move percentile/lookback/definition, alter LONG direction, entry/hold/overlap/costs, remove years, add filters, switch exchange/source or select favorable subperiods under this MVE ID. Materially different mechanism => new MVE ID + new prospective authority.

## User authorization
After V0.4 SOURCE_DATA_PASS, user explicitly authorized: `ATACA DISCOVERY`. This authorizes only this one-shot 2021-2024 Discovery, not 2025/2026, live trading, exchange mutation, main merge, or deployment.
