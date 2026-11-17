# STABLE-003 — prospective cash-and-carry: PRE-DATA scientific freeze
Date: 2026-11-17 (Europe/Zurich). Status: protocol only; NOT live, no market sample collected and NO profitability proven.

## Scope and leakage control
- Exchange candidate: OKX, BTC-USDT and BTC-USDT-SWAP; secondary independent replication ETH-USDT and ETH-USDT-SWAP only after primary gate. This is spot-long + matched USDT-linear perpetual-short, NOT the prior OKX linear-vs-inverse two-perpetual Funding Hunter.
- Prospective observation starts ONLY after this file's commit timestamp. Previously viewed 2025 archive and 2026 snapshots are development evidence, never independent OOS. Do not backfill an observation after missing collection.
- Research/paper only. No account, orders, keys, wallets, margin changes, Render deployment, money movement, exchange login, or merge into main.
- The protocol may not be altered after observing outcomes; any amendment generates a newly tagged experiment and invalidates OOS credit on data previously seen.

## Data provenance and fail closed
- Immutable collection record for every candidate snapshot: exchange server time, collector UTC time, request URI (no secrets), HTTP status, response SHA256 and raw source timestamp, instrument metadata (contract size, lot/tick, margin mode), official funding settlement timestamp/rate (actual, not predicted), funding next payout; paired spot/perp bid/ask at synchronized timestamp plus depth at estimated trade size, mark and index, FX conversion as applicable.
- Reject when bid/ask quote age > 2s, spot/perp observation skew > 1s, inverted books, stale funding, missing metadata, missing source hashes, missing side depths, unavailable fee schedule, unexpected instrument status, or nonmonotonic timestamps. Never infer fills from midpoint or last trade.
- Fees: dated/account-specific verified tier, all FOUR entry/exit spot/perp taker executions as conservative baseline; no maker rebate assumption; spread included through ask-buy / bid-sell on spot and bid-short / ask-cover on perp; full depth VWAP at a predefined size. Funding marked at each observed actual settlement, signed correctly; account for adverse funding and basis; funding amounts and collateral flows computed in the actual settlement currency.
- Nonpublic account-specific fee rates and collateral constraints remain uncertified until independently evidenced; if not evidenced classify SOURCE_BLOCKED / COST_UNCERTIFIED, no pretend true PnL.

## Frozen comparison (no parameter hunt)
- Notional: 1000 USDT per leg, with adequate separate collateral and cash reserve modeled; report return on *all* committed capital, not on perp margin only. No leverage enhancement.
- Paper shadow A: continuously hedged from first valid synchronized executable quote, rebalance only under predeclared exchange contract quantity tolerances; evaluation horizons 7,14,30 calendar days with bid/ask executable liquidation at each endpoint.
- Paper shadow B: same instrument, notional, price, fees and horizons; open ONLY if latest actually settled (past) funding, annualized conservatively over known elapsed interval with zero favorable extrapolation beyond next 8h in stress, clears full round-trip verified taker cost + 10bps extra buffer on a 7-day carry projection; otherwise FLAT. Any future unknown funding paid cannot be used at entry. No optimization after observing.
- Simulate both from a single timestamped incoming source stream. Any observed profitable trade is descriptive until all marks, payout and exit execution verified.

## Predefined result metrics
For every candidate entry and horizon: quote availability/age, actual two-leg matched units, entry cost, realized actual funding events, exit quote and VWAP, spot PnL, perp PnL, basis PnL, total fees, net PnL, gross committed capital, net return, liquidation distance and adverse margin excursion. Include zero-trade days and failed coverage in denominator.
- Compare with no-trade cash baseline; report count, exposure days, proportion positive, drawdown, funding sign reversals, stress taker/slippage + 10bps and + 30bps round trip extra, forced close during worst observed basis and venue outage assumptions.
- Never call a zero-signal/zero-trade experiment profitable; no claim of independent forward edge if dates observed during tuning.

## Hard promotion gate (predeclared)
- Scientific SOURCE_GO: >99% timely matched valid quotes across a continuous 30-day observation window, plus complete official actual funding events, reproducible hashes, dated fee/contract specs and executable depth for all 4 legs.
- Economic CONDITIONAL_GO (research only): after all verified costs, at least 30 calendar days prospective, 5 complete non-overlapping independently evaluated 7-day windows OR declare sample insufficient (30 days cannot contain 5 such windows: therefore **minimum 35 days** for this gate), positive median net PnL per exposure-day AND positive aggregate net PnL, survives +10bps total execution-cost stress, no margin-liquidation breach under observed path, complete collateral simulation. If any fails => NO-GO/INSUFFICIENT, never live GO.
- 14/30-day horizon results overlap windows and are supplementary, not independent samples; 35 days alone cannot establish future consistency. Even a positive gate is only candidate for replication in a later, unobserved window, not permission to trade.
- Status labels: SOURCE_BLOCKED, COLLECTING (only if observed), SCIENTIFIC_NO_GO, ECONOMIC_NO_GO, CONDITIONAL_REPLICATION_CANDIDATE. No claim of stable income or guaranteed profit.

## Current finding
As of freeze creation, no verified synchronized live spot+swap quotes have been collected in this run. A publicly opened ticker response was a stale ~3-month cached snapshot and was deliberately excluded. Official public API documentation exists, but prospectively executable data collection and account fee eligibility remain open gates.

## Prior work, distinct strategy
- Funding Hunter V01 PR #252 SOURCE_BLOCKED; V03 PR #255 rebuilt six 2025 books QUOTE_ONLY; V04 PR #256 28 June 2025 linear/inverse differential signals FLAT. These do NOT constitute spot+perp evidence.

Next required action: independently verify reliable continuously timestamped read-only data collector and dated executable 4-leg quote/fee inputs, then start NEW prospective observation with strict receipts. No live trading.
