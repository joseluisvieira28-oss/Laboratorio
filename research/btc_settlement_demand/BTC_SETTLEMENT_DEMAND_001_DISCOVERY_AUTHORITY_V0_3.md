BTC-SETTLEMENT-DEMAND-001 — DISCOVERY AUTHORITY V0.3
MVE_ID: BSD-WOW7D-1D-001
DATE_FROZEN: 2026-09-14
STATUS: FROZEN PRE-OUTCOME / ONE-SHOT DISCOVERY AUTHORIZED

GOVERNANCE
Research-only. Fail-closed. No live trading. No exchange mutation. No POST/PUT/PATCH/DELETE exchange actions. No merge to main. No Render deployment. No post-outcome tuning. No cherry-picking. 2025 LOCKED. 2026 LOCKED. No holdout access in this Discovery.

SOURCE AUTHORITY
Canonical source gate: BSD-TXCOUNT-002
Source family: Blockchain.com Charts — Confirmed Transactions Per Day (n-transactions)
Source Gate run: 34864390599
Source Gate artifact: 10355248843
Source Gate artifact ZIP SHA256: d58b3e06683d827f393760112927b8c9314cdfdfb6ae559fbf1301b29383f163
Drive evidence ZIP: 1BeD-hxSccO4n9XDiGmJ7gh1rZDJ4BNvk
Raw source SHA256: e0488714ce6023589de3e9cd15524c5f1e643a0ae0028147c8cb830b313ffa7f
Source manifest SHA256: 108525b5d3c3f331f8aef4dbcfcec05c8ab0221ba7c8cbc179d8c944c239b9cd
Source coverage: 2017-01-01 through 2024-12-31, 2922/2922 UTC days, zero missing.

HYPOTHESIS / MECHANISM
Confirmed Bitcoin transaction activity is treated as realized settlement/network demand. A sustained week-over-week acceleration in confirmed transaction count is expected to be directionally bullish for BTC; a sustained week-over-week deceleration is expected to be directionally bearish. This mechanism is distinct from miner hashrate/difficulty, stablecoin supply, funding/OI, options skew, macro sign regimes and OHLC indicators.

SIGNAL — FROZEN
For each source observation day t:
RECENT7(t) = arithmetic mean of n-transactions over t-6 ... t.
PRIOR7(t)  = arithmetic mean of n-transactions over t-13 ... t-7.
ACCEL(t)   = RECENT7(t) / PRIOR7(t) - 1.

Direction:
ACCEL(t) > 0  => LONG (+1)
ACCEL(t) < 0  => SHORT (-1)
ACCEL(t) = 0  => NO TRADE

No threshold, percentile, z-score, volatility filter, regime filter, weekday filter, volume filter, fee filter, price filter or alternative smoothing is authorized.

TIMING — FROZEN
Signal uses only source data through the completed UTC day t.
A full one-calendar-day publication/availability buffer is mandatory.
Entry = BTCUSDT daily OPEN at 00:00 UTC on t+2.
Exit  = BTCUSDT daily OPEN at 00:00 UTC on t+3.
Hold = exactly 1 UTC day.
No intraday optimization.

DISCOVERY WINDOW — FROZEN
Eligible entries: 2018-01-01 through 2024-12-30 UTC.
Eligible exits: no later than 2024-12-31 00:00 UTC.
Any trade requiring a 2025 timestamp is forbidden and must fail closed.
2025 and 2026 must not be downloaded, parsed or inspected.

MARKET OUTCOME SOURCE — FROZEN
Official Binance Data Vision monthly BTCUSDT 1d klines only.
Months: 2018-01 through 2024-12 inclusive.
Required market fields for outcomes: open_time and open only.
Other kline columns may be physically present in official archives but are not to be used as predictors, filters or tuning inputs.
No alternate exchange or stitched market source.

RETURN — FROZEN
raw_return = exit_open / entry_open - 1
gross_signed_return = side * raw_return
gross_bps = 10000 * gross_signed_return

ROUND-TRIP COSTS — FROZEN
NET6  = gross_bps - 6 bps
NET10 = gross_bps - 10 bps  [PRIMARY]
NET20 = gross_bps - 20 bps
Costs apply once per non-flat trade. No cost rescue.

DISCOVERY STATISTICS — FROZEN
N trades; long/short counts; mean and median gross bps; mean NET6/NET10/NET20; NET10 profit factor; NET10 win rate; calendar-year NET10 means; 2021-2024 stability; bootstrap distribution of mean NET10 using seed 20260914 and 10,000 resamples; bootstrap p(mean NET10 <= 0); 95% bootstrap CI; positive-year gross contribution concentration; cumulative NET10 and max drawdown as diagnostics.

PROMOTION GATES — ALL REQUIRED
1. N >= 1000.
2. Mean NET10 > 0 bps/trade.
3. NET10 profit factor > 1.00.
4. Median gross return > 0 bps/trade.
5. At least 5 of the 7 calendar years 2018-2024 have non-negative mean NET10.
6. At least 3 of the 4 calendar years 2021-2024 have non-negative mean NET10.
7. Bootstrap p(mean NET10 <= 0) <= 0.20.
8. Maximum positive-year gross contribution share <= 70%.
9. Source binding, timing firewall and protected-period firewall all PASS.

TERMINAL DISCOVERY STATES
DISCOVERY_PASS_CANDIDATE — all frozen promotion gates pass. This does NOT authorize live trading or 2025/2026 holdout access.
DISCOVERY_FAIL_NO_PROMOTION — one or more frozen economic/statistical gates fail.
TECHNICAL_FAILURE_PREOUTCOME — implementation/preflight failure before market outcome access.
DATA_FAILURE — required frozen source/market data invalid or incomplete.
PROVENANCE_FAILURE — wrong source bytes, unexpected schema, protected-period access or authority mismatch.

NO-RESCUE RULE
If this MVE fails, do not invert it, add thresholds, change 7/7 windows, change publication buffer, switch long-only, change hold, change costs, remove years, add filters, change exchange, add fees/volume, or select a favorable subperiod under this MVE ID. Any materially different mechanism requires a new MVE ID and new prospective authority.

USER AUTHORIZATION
After SOURCE_DATA_PASS was reported, the user explicitly authorized: “AVANCA COM TUDO MANO ATACAAAA”. This authority treats that as authorization for the one-shot 2018-2024 Discovery only under the frozen rules above. It does not authorize 2025/2026 or live trading.
