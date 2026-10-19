# CRYPTO LAB FUNDING HUNTER V01 — pre-outcome protocol
Frozen 2026-10-19. Research only. Base investigation: funding-dispersion-deltaneutral-v0.1 @ 637c583fd9f862dfd22960926d094eb95b29eb4b.
No mission market outcomes have been opened. This protocol does not reopen any parent hypothesis or the protected 2026 holdout.

## Mechanism and prior audit
Carry persistence between MEXC and Binance linear USDT perpetual futures, SHORT the venue with higher lagged settled funding per hour and LONG the lower. Distinct from directional CONVEX, but NOT a novel economic family: FUNDING-DISPERSION-DN-001 already preregistered this mechanism on Bybit/OKX.
This is a venue replication with a full cashflow/cost gate, not an independent discovery or risk-free arbitrage.
Audited parent freezes/receipts at 637c583fd9f862dfd22960926d094eb95b29eb4b; MEXC interval source closeout at 12c17e2c657dd4c23e9e707349ee548a73aa06d0; CVFB final status at 113fc8950f02688b4e09ee24a76b401cf293fcd8.
CVFB involved Binance/Hyperliquid, BTC/ETH, and failed exact oracle provenance; it does not establish this venue pair's edge. MEXC interval-event study was blocked on announcement article bodies; calendar-event selection is not used here.

## Immutable retrospective universe
All BTC, ETH, SOL mandatory, no dropping. MEXC BTC_USDT, ETH_USDT, SOL_USDT; Binance BTCUSDT, ETHUSDT, SOLUSDT. Linear perpetuals margined and settled in USDT only. Historical contract multipliers, lot/tick sizes and identity require public dated evidence; current metadata cannot prove historical identity.
Warmup 2024-12-31T00:00:00Z through 2024-12-31T23:59:59.999Z.
Evaluation 2025-01-01T00:00:00Z through 2025-12-31T23:59:59.999Z.
Entry each day 00:05:00 UTC; exit next day 00:05:00 UTC. Last entry 2025-12-30, last exit 2025-12-31 (no 2026 access). Equal capital weight 1/3 per asset, independent sleeves, no overlapping episodes per asset.
At entry use only last settled rates with timestamps strictly before entry, actual previous interval in {1,4,8} hours, both observations <=8h old. Normalize rate/actual elapsed hours. Missing transition evidence or unsupported interval blocks the dataset; do not treat a missing settlement as a longer interval.
Threshold abs differential >=0.5 basis points/hour. Ties/below threshold: flat. No grid, asset selection, reverse-orientation rescue, leverage optimization or extension of dates.
Sign is fixed for 24h: positive MEXC-minus-Binance => short MEXC, long Binance. Reversals during holding are charged in full, never retroactively flip. Every venue settlement with entry < timestamp <= exit is included independently; no assumption that venues settle together. Exact epoch milliseconds and UTC representation must be retained and hashed before economic aggregation.
Actual dated schedules are to be evidenced, not invented as universal 00/08/16 UTC. Freeze rules first; publish the exact source-derived settlement manifest before calculating outcome cashflows. No latest funding calls returning protected 2026 rows.

## Positions and accounting
Hypothetical total initial capital E=2000 USDT per asset sleeve, 1000 pre-funded on EACH venue; no borrowing, transfers, compounding or cross-venue margin netting. Each leg target entry notional N=1000 USDT. Match base quantity after contract multiplier and floor to common executable lots; residual base delta <=0.1% of target quantity, otherwise block. No invented fills.
s=+1 long, -1 short. Venue funding cashflow at settlement k = -s*q*multiplier*P_settlement[k]*realized_rate[k]. Positive funding means longs pay shorts. Negative reverses. Public settled rate is not a private account payout: label all resulting cashflows hypothetical reconstructed, never actual received payouts.
Trading PnL = sum(s*q*multiplier*(exit_fill-entry_fill)). Net adds all funding and subtracts four execution commissions, exactly once each on actual fill notionals.
For matched q, long A/short B price component = q*((A_exit-B_exit)-(A_entry-B_entry)); adverse widening of short-minus-long basis loses money.
Historical bid/ask/depth at entry/exit is required. Mid/mark/OHLC cannot be called executable. Buy ask/sell bid plus size impact; no double-counting spread already in fill.
Funding valuation requires exact official settlement mark/fair price or documented equivalent at the precise charge timestamp; a candle close or nearest observation is not equivalent.

## Cost assumptions, fixed before outcomes
Conservative scenario, NOT certified historical/account fees: Binance taker 5bps each execution; MEXC taker 6bps each execution. Four legs = 22bps of one-leg N at equal unchanged notionals. No VIP, token discounts, rebates or zero-fee promotion credit.
Baseline additional spread+slippage reserve: max(observed all-in execution shortfall, 2bps per execution); total floor 8bps, total fee+execution floor 30bps*N. Stress reserve 7bps each, total 50bps*N.
If dated applicable public fees exceed assumptions, source gate fails; do not silently amend. Retrospective historical fee coverage still mandatory.
Basis and funding reversals are separate PnL terms, not covered by the reserve. Margin stress: each venue must survive +/-50% independent mark excursion plus its dated maintenance margin and funding deductions with its own collateral; also model venue outage, legging, ADL and contract multiplier rounding. Margin not transferable during stress. A delta-neutral aggregate can liquidate on one venue.

## Source gate (fail closed before economics)
Public/free/unauthenticated GET and public documentation only. No accounts/keys/login/wallets/orders/Render/Windows operator. No paid data or requester-pays.
Require all 3 assets and both venues, dated contracts/fees, complete realized settlement histories including prior event for each interval, exact settlement valuation prices, historical paired executable books/depth and timestamps at every entry/exit, dated maintenance-margin rules and official geographic product availability.
Raw receipts: canonical URL, retrieval UTC, HTTP status, SHA256 bytes, schema, completeness/coverage, duplicates/conflicts, units, contract mapping, settlement manifest hash. HTTP 200 alone is not PASS.
Reject HTML/error/empty/truncated payloads, nonfinite numbers, duplicate timestamps, out-of-window market records, missing symbols, unknown units, estimates presented as settled and incomplete pagination. No forward/nearest/back fill or fabricated zero.
MEXC documented history pagination has no documented start/end selector; do not fetch latest pages containing 2026. Require legitimate pre-2026 bounded archive/index first.
Missing exact prices/books/fees => SOURCE_BLOCKED; do not calculate a partial funding-only profit and promote it.
Documentation review can establish a source block without opening outcomes. A source block is not economic NO-GO.

## Economic verdict if and only if all sources pass
Retrospective only, no OOS credit. Report all episodes, daily marked PnL, separate funding/basis/fees/spread/impact, immobilized-capital return, worst sleeve drawdown, margin stress, asset/year-half concentration, and all missingness.
NO-GO if net <=0 for any asset or pooled, either half-year pooled <=0, <30 trades per asset, one asset >50% of positive net profits, stress net <=0, or 95% lower bound of pooled mean daily net <=0 using 10000 moving-block bootstrap resamples (7-day blocks, seed 19012025). Report multiple dependence and selection caveats.
Only all-gate survivor => CANDIDATE_PENDING_FORWARD, never proven profitable.

## Independent forward validation design (inactive until survivor)
Separate preregistration and immutable commit BEFORE collection, at least 90 future UTC days and 30 episodes/asset, fresh public paired books and settlement evidence. A new explicit forward dataset must be separated from protected 2026 holdout; no automatic 2026 access is authorized here. Same assets/threshold/orientation/24h horizon/cost stress, no tuning, no peeking decisions; fixed terminal review and outage rules. Append-only timestamped/hash-chained observations, missingness charged as failed validation, independent frozen evaluation process. No trading authority.
If no survivor, do not start collection. Stop V01; source repair requires a new version frozen before new outcomes.
