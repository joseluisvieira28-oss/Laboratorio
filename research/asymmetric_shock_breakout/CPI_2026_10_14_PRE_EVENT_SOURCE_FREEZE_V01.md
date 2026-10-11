# CPI 2026-10-14 — prospective public market-data observation v0.1
Status: PRE-EVENT_SOURCE_ONLY_FREEZE
Official source: https://www.bls.gov/schedule/2026/10_sched_list.htm
Independent scheduled event: 2026-10-14 08:30 ET = 12:30 UTC.
Source only: MEXC public BTC_USDT and SOL_USDT BBO.
Fixed slots: every 5 seconds from 12:29:00Z through 12:33:00Z inclusive (49 per symbol).
Start later than the first slot => MISSED_PROSPECTIVE_SOURCE_WINDOW.
Clock: public MEXC server-time drift <= 2000ms; quote freshness <= 10000ms.
No fill-in for missing quotes; crossed or invalid books are invalid.
Source pass: >=47/49 valid each, pre/post event coverage, monotonic versions, max gap <=10 seconds.
Other states: BLOCKED_CLOCK, SOURCE_COVERAGE_BLOCKED, TECHNICAL_FAILURE.
Persist immutable source counts, raw public quote receipts and data hashes.
No trading signals, return calculations, backtest, market orders, accounts, wallets, expenses,
alteration of other studies, merge to main or post-outcome optimization.
No economic verdict is permitted. No automatic activation.
