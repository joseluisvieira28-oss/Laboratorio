# Three-family audit and Adaptive DCA preregistration V1
Created 2026-10-22; effective freeze is this file's Git commit, not its prose date.
Scope: research only. Main preserved; no orders, wallets, private exchange calls, spending, automation, deployment or promotion.

## Exposure before freeze
Prior reports already read: TOKEN-UNLOCK-EVENT-001 official NO_EDGE; DCV-001 DISCOVERY_FAIL; FUNDING-SQUEEZE V03 NO_EDGE_LOWCOST. Their tested hypotheses will not be rerun or renamed. Historical crypto market direction and several other laboratory results are known. Historical DCA splits below are temporal OOS for this fixed rule, NOT proof of laboratory-wide untouched outcomes. Reading old results is audit work, not a new preregistration of those old tests.

## Deduplication decision
Token Unlock Supply Shock overlaps TUE-CLIFF-ADV30-001; use existing receipt and audit provenance/cost/control limitations. No rescue of the failed threshold, horizon or sign.
Funding Crowding overlaps DCV-001 (funding x OI x realized volatility); use existing receipt. Funding carry/squeeze is adjacent, not identical; preserve its separate negative economic verdict.
Adaptive DCA: no DCA/adaptive branch-name match in 1,023 branches, nor DCA in Sep18 census. This is bounded evidence, not a proof all bytes in all branches were searched. Exact new specification below receives a distinct audit ID ADCA-BTC-SMA200-001.

## Hypothesis and frozen rule
At equal external contributions, contrarian accumulation after below-SMA200 days may improve terminal net wealth versus fixed weekly DCA.
Asset/venue fixed BTCUSDT Binance Spot. Long only, no leverage, no shorts, no funding.
Acquire only daily OHLCV 2020-01 through 2025-12 official monthly ZIPs and SHA256 sidecars. Do not download 2026 outcomes.
Each calendar year 2021..2025 is a separate empty portfolio; deposit exactly 100 USDT each Monday at 00:00 UTC; cash zero interest primary.
Signal uses previous completed daily close vs arithmetic mean of the 200 closes strictly before Monday.
Buy budget 150 if close < SMA200, otherwise 50; buy min(cash, budget). No borrowing. Unspent cash retained. No retuning/catchup at terminal.
Comparator fixed weekly DCA invests min(cash,100). Non-signal delayed-cash control invests min(cash,75). Cash-only control retained.
Execution reference Monday daily open (model, not demonstrated executable quote). Liquidate at Dec31 daily close with sell friction.
Deduct 15bps of gross notional on EACH buy and terminal sell; stress 30bps each side. Cash outlay includes fee: units = spend/[price*(1+c)]. Sell proceeds=units*price*(1-c).
15bps is a scenario (10 fee+2.5 half-spread+2.5 slippage), not verified account fee. Stress=20+5+5bps. Capacity not established; no GO even on positive candle results.
Report total fees/friction, turnover, terminal cash, units, net wealth, gain divided by contributions, and daily cash-flow-adjusted time-weighted maximum drawdown.
Development 2021-23 descriptive only, no parameter selection; 2024 validation and 2025 temporal test opened once after freeze and implementation tests.
Primary effect each year: (adaptive net terminal wealth - fixed DCA net wealth)/total external contributions.
No pooled daily pseudo-replication: annual paths overlap market regimes and 2 OOS years are insufficient to establish robust statistical edge.
Positive historical candidate requires positive primary effect in BOTH 2024 and 2025 at primary AND stress cost. Otherwise historical superiority not replicated. Regardless of gate result: no confirmed independent economic edge without prospective/executable evidence.
No bootstrap of weekly purchases treated as independent trades. No multiple-indicator sweep.

## Data gate and controls before outcomes
72 ZIPs+72 official sidecars, SHA256 match, strict ascending unique UTC daily timestamps, complete 2192 days 2020..2025 (leap 2020,2024), valid positive OHLC and nonnegative volume. Fail closed on missing/conflicting rows, timestamp units (ms before2025/us since2025), bad checksums.
Document observed archive retrieval time, source time, parser and runner hashes. Provider may revise archives; hashes establish retrieved version, not historical publication vintage.
Synthetic tests before real calculation: flat-price fee accounting, no-lookahead signal, contribution equality/cash conservation, no leverage, timestamp unit equivalence. Separate implementation corrections from strategy amendments; any economic rule change requires new prospective study.
Source URLs: https://github.com/binance/binance-public-data/blob/master/README.md and https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-YYYY-MM.zip (+ .CHECKSUM).
Total monetary research acquisition budget zero; use existing local runtime and public data. Record actual downloads/bytes/time; trading-cost totals require actual ledger.
## Independent family decisions
Each family receives its own report and status. SOURCE_BLOCKED/INSUFFICIENT != NO_EDGE. Historical inherited failures apply only to exact tested mechanisms. No family-wide universal rejection.
