# USOPEN-STRADDLE-001 — U.S. OPEN ATM STRADDLE MONETIZATION — RETROSPECTIVE PRICE-ONLY PRE-FREEZE

Date frozen: 2026-09-24
Parent mechanism: `USOPEN-PERSIST-001`
Status: PRE_DIAGNOSTIC_FROZEN
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Promotion credit: ZERO
Live execution: FALSE

## Purpose

Test whether the already-discovered U.S.-open volatility regime is even economically compatible with a simple long-vol implementation before spending money on historical executable options data.

Because the 2024 U.S.-open realized-volatility behavior is already known and helped motivate this monetization question, this study is explicitly **retrospective/contaminated** and can never promote the strategy. It is only a kill-or-continue economic diagnostic.

## Public source

Use the exact public Cryptarbitrage/Deribit BTC-options parquet already recovered and hashed by BTC-OPTIONS-VRP-001:
- Google Drive file id: `1g9p2Kq8op40y4ZFQQ9AJw8a9CaDThOY8`
- title: `btc_option_data_toshare.parquet`
- period: 2024-01-13 through 2024-07-27
- historical BTC option snapshots with bid/ask prices;
- no bid/ask size columns.

Absence of displayed sizes means this MVE can assess **per-unit price economics only**, never executable capacity.

## Frozen trade construction

Eligible days:
- regular U.S. cash-market weekdays inside source coverage;
- exclude full-day NYSE closures.

Time zone:
- `America/New_York`, DST-aware.

Entry:
- exact 09:00 ET snapshot;
- choose nearest eligible expiry with 7 <= DTE <= 14;
- within that expiry, choose a same-strike call+put pair minimizing absolute log(strike / underlying_price);
- require positive non-crossed bid/ask on both legs;
- BUY call at ask + BUY put at ask.

Exit:
- exact 11:00 ET snapshot;
- exact same call and put instruments;
- require positive non-crossed bid/ask on both legs;
- SELL call at bid + SELL put at bid.

One episode per eligible date. Never widen timestamps.

## Cost model

Per 1 BTC option amount on each leg:
- historical standard Deribit option fee: 0.0003 BTC per option trade side;
- fee cap: 12.5% of option premium per trade;
- four option trades per episode (2 entry + 2 exit);
- bid/ask crossing is already embedded in ask entry and bid exit;
- no delivery fee because positions are closed intraday.

Base net BTC:
`exit_bid_call + exit_bid_put - entry_ask_call - entry_ask_put - all_fees`

Stress:
- base net minus one additional bid-ask spread per leg across the round trip, defined prospectively as max(entry spread, exit spread) for that leg, adverse only.

## Frozen diagnostic gates

Minimum executable episodes: 50.

A result is `RETROSPECTIVE_PRICE_ONLY_PROMISING_FORWARD_TEST_JUSTIFIED` only if:
- mean base net BTC > 0;
- base profit factor >= 1.20;
- date-bootstrap 95% lower bound of mean base net BTC > 0;
- at least 4 calendar months have nonnegative mean base net;
- mean stress net BTC > 0;
- stress profit factor > 1;
- largest positive episode contributes <= 25% of total positive PnL.

Otherwise:
- `RETROSPECTIVE_PRICE_ONLY_NO_SUPPORT`, or
- `PRICE_ONLY_SAMPLE_INSUFFICIENT`.

Passing grants **zero promotion credit**. It only justifies a separate prospective public-BBO forward MVE.

## Firewall

Forbidden:
- changing 09:00/11:00 after outcomes;
- changing 7–14 DTE after outcomes;
- choosing a different strike rule;
- mid-price fills;
- removing fees;
- selecting profitable weekdays/months;
- excluding losing episodes;
- changing long-vol to short-vol;
- using 2025 or pre-boundary 2026;
- claiming executable size;
- live trading;
- exchange mutation;
- merge to main.
