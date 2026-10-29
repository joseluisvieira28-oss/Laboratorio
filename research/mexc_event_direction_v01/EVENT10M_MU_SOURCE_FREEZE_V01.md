# EVENT-10M MU — SOURCE-FIRST FREEZE V0.1 (2026-10-29)

Product scope: ONLY Micron Technology Nasdaq stock MU and MEXC internal MUSTOCK_USDT. The public MEXC perpetual description identifies MU as Micron. Do not treat MLIUSDT in the screenshot as MU; MLI identity is UNVERIFIED. Exclude NVIDIA (separate chat) and SPCX (SpaceX-related private/tokenized exposure, not a Nasdaq common-share opening auction).

FROZEN source-only test: October 26 and October 27, 2026, each US/Nasdaq opening 09:30-10:10 America/New_York (13:30-14:10 UTC on both dates). This time interval is historical Discovery, previously studied as MEXC-index 5min data; NOT independent OOS. Exactly two public sources:
- Yahoo Finance UNOFFICIAL unauthenticated MU chart endpoint, interval 1m, period 2026-10-26T00Z to 2026-10-28T00Z, no bypass if rate-limited. This is NOT primary/official Nasdaq data and NO point-in-time timestamp custody.
- MEXC publicly accessible standard-futures INDEX KLINE MUSTOCK_USDT interval Min1, requests only for each of those two UTC calendar days. This index is NOT the MEXC Event Futures server openPrice or settlement.
Demand HTTP 200, JSON schema, aligned unique 60-second timestamps, finite positive open prices. For EACH day require >=30 of 40 expected bars on each independent source and >=30 1m aligned timestamps across both sources. Missing values never imputed; no substitute source, date, symbol, timeframe or alias.

Save exact raw-response SHA256, source URLs, coverage, missing minute timestamps, failure reasons. Do NOT calculate market return, stock-index spread, lead-lag, directions, signal, PnL, historical payout or economic outcome in this stage. A SOURCE PASS is only historical feasibility, not proof of 10m forecast advantage or collector as-of eligibility.

Any subsequent study requires separate scientific freeze BEFORE its outcomes; contemporaneous real MEXC Event Futures payout and shadow-to-executed-price parity remain open gates. Original prior NO_EDGE/source-blocked investigations and protected September 2026 holdout remain unchanged. No NVIDIA or SPCX tests, real orders, account, keys, private requests, money, paid sources, main merge or trading.

Nasdaq official trading hours: https://www.nasdaq.com/market-activity/stock-market-holiday-schedule
MEXC MU stock/perpetual description: https://www.mexc.com/futures/MUSTOCK_USDT
