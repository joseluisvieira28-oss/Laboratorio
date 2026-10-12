# CONVEX-MULTIASSET-4R-HIST-001 — CLOSEOUT 2026-10-12
**SOURCE_PASS_5_OF_5 / HISTORICAL_DIAGNOSTIC_FAIL / NO_PROMOTION / NO_LIVE_AUTHORITY.**
The fixed 4R exit lost money in the frozen historical five-asset portfolio. This failure is economic, not a source failure. No hypothesis, fee, timer, universe or gate was changed after outcomes.

## Binding receipts
- Original ETH/SOL branch remains cda99a6ae2f34d7d4789db027cc0b22f70255b19; only additive new experiment files.
- Preregistration ec30dc6353e2880519ff31f06f076a0b33ed05be committed before source/results.
- Execution checkout verified in logs: 3685c61ef29c3376ded984e86632f186e955fe01.
- Actions run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38292841900, job 114956790898; 7/7 tests passed.
- Artifact https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38292841900/artifacts/11766534195; 21,710,855 bytes; ZIP SHA256 0cbd6bb7e89c5977b703b6e533fa2d842ffb996f360f3d3e181fb636412e1094.
- ZIP contains 1312 files: raw official downloads and CHECKSUM bytes, URL/hash manifest, five normalized market/funding datasets, complete six-arm trade ledgers/report and custody hashes. Artifact retained 90 days through 2027-01-10. Downloaded local ZIP independently matched digest; all 1311 custody entries verified. Equity conservation checked for every arm.
- Engine SHA256 72bf672e76e1b68c51ed0140a8650a0e2bba4bb6604c8aba2918da36d66b32d4; reused Parent helper SHA256 74eb146c34103267fbb5b8d1ad96140fc8af9b39c01c36e52c5950976d84a9f0.

## Source gate
Each of XRP/DOGE/ADA/LINK/AVAX: 43,824/43,824 economic UTC hours, December 2020 warmup, 5,478 official funding events; no imputation. Official Binance UM monthly/daily hierarchy with mark prices, timestamp normalization <=1000ms, <=9h funding gap; downloaded ZIPs matched official CHECKSUM. All five source gates PASS before portfolio scoring.
This is public Binance Futures historical source with prescribed MEXC 8bps/side fee scenario. It is NOT a historical MEXC market/funding/execution reconstruction.

## Primary shared account results
Initial 500 USDT, planned .25% entry risk/.50% aggregate, 1x full collateral; no deposits/rebalancing open positions. Simultaneous opportunities in fixed universe order, one position per symbol. Remaining aggregate risk can cap a later entry size; entries resize only using current marked equity.

| Metric | BASE 2bps/side | STRESS 5bps/side |
|---|---:|---:|
| Final equity USDT | 411.621501 | 399.083289 |
| Net USDT | -88.378499 | -100.916711 |
| Return | -17.675700% | -20.183342% |
| Closed trades | 772 | 769 |
| Win rate | 18.134715% | 17.945384% |
| Net profit factor | 0.841138 | 0.817282 |
| Realized mean win/mean loss | 3.797138 | 3.736994 |
| Close-based MTM drawdown | -19.944388% | -20.974883% |
| Maximum losing streak | 32 | 32 |
| Net excluding largest winner USDT | -93.340538 | -105.868230 |
| Funding cashflow USDT | -20.879693 | -20.831517 |
| Fees USDT | 25.450643 | 24.984483 |
| Targets / stops / forced end | 140 / 631 / 1 | 138 / 630 / 1 |
| Risk/collateral rejected opportunities | 396 | 418 |

No gap-stop or timer exits occurred in the primary arms; these paths remain tested engine behavior rather than observed historical cases. Stop-first applied on each ambiguous OHLC bar. Exit trade timestamps identify the enclosing UTC hour, not an invented exact intrabar time.

## Per-symbol primary attribution
These are shared portfolio contributions, NOT returns on five independent 500-USDT accounts.

| Symbol | BASE trades | BASE net USDT | BASE PF | STRESS net USDT |
|---|---:|---:|---:|---:|
| XRP | 148 | -25.870854 | .784748 | -36.294403 |
| DOGE | 157 | -26.005858 | .785054 | -25.502010 |
| ADA | 159 | -22.573188 | .805666 | -26.456633 |
| LINK | 160 | -29.209390 | .741853 | -28.963411 |
| AVAX | 148 | +15.280790 | 1.178015 | +16.299746 |

Positive contributors: 1/5. AVAX cannot be selected after outcomes to convert the frozen family failure into PASS.
BASE annual PnL USDT: 2021 -61.321344; 2022 -31.514755; 2023 +27.456431; 2024 +1.717459; 2025 -24.716291. Positive isolated years do not rescue the total failure.

## Prespecified larger-risk diagnostics
| Entry risk / aggregate cap | BASE ending equity | STRESS ending equity | BASE return | STRESS return |
|---|---:|---:|---:|---:|
| .50% / 1.00% | 332.304736 | 312.438268 | -33.539053% | -37.512346% |
| 1.00% / 2.00% | 204.559500 | 180.979660 | -59.088100% | -63.804068% |
Increasing risk worsened account survival; no leverage benefit inferred.

## Frozen adjudication
Primary BASE net>0 FAIL; STRESS net>0 FAIL; BASE/STRESS PF>1 FAIL; realized BASE payoff>=4 FAIL; positive net excluding largest winner FAIL; >=3/5 positive symbols FAIL (1/5). Source completeness PASS (5/5).
**HISTORICAL_DIAGNOSTIC_FAIL.** Even without the payoff threshold, negative net and PF<1 independently reject profitable performance on this sample.

## Scope and integrity
2021–2025 has ALREADY been seen in the Parent family; this is historical diagnosis of a new exit, NOT independent family OOS. Previously negative Parent expansion remains CROSS_SECTION_EXPANSION_FAIL; the original ETH/SOL design/source CI did not test 4R economic outcomes.
Funding/slippage are documented historical/model costs, not actual fill evidence. OHLC conservative barrier assumptions, fixed spread/impact allowances and fractional quantities cannot prove executable MEXC fills, minimum lots, account fee tier or intrabar liquidation. No leverage-specific result claimed; drawdown is at completed bar closes and can understate intrabar loss.
No shadow wait was imposed. No orders, real trading, private API, credentials, wallets, money, Render deploy, main merge or protected 2026 source opened.
