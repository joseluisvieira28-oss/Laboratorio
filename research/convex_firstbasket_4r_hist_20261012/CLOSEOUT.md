# CONVEX-FIRSTBASKET-4R-HIST-001 � CLOSEOUT 2026-10-12
**HISTORICAL_DIAGNOSTIC_FAIL / HISTORICAL ONLY / NO PROMOTION / NO LIVE AUTHORITY.**

All primary net/PF/asset-positivity and top1 robustness gates pass. The ONLY failed gate is BASE realized payoff >=4. Thus this window was profitable after costs; FAIL describes the full inherited 4R hurdle, not negative economic expectancy.

## Binding execution and custody
- Freeze before outcomes: 48d174edd94bc8ede3fe96c9b1d5b65312ebdb0b.
- Execution checkout: 5ed4860a4582151588e4228f1d61d50e16ef26c8; run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38294457980; job 114962086290; 7/7 invariant tests passed.
- Artifact ZIP SHA256: 21615685e41e5ec0ac6f38307a7b15e6713d5fcb955e46c717b4e54c0ce243b8; independently verified 793 custody entries; equity conservation checked for every scored arm.
- Engine SHA256 4e67ea01d19d4df02e0f3476d7d23c3aa779ee00fa3421d38d8827961f37670c; unchanged Parent helper SHA256 74eb146c34103267fbb5b8d1ad96140fc8af9b39c01c36e52c5950976d84a9f0.
- Prior five-asset artifact ZIP independently verified against 0cbd6bb7e89c5977b703b6e533fa2d842ffb996f360f3d3e181fb636412e1094; all 1311 custody entries and six-arm account conservation passed.

## Sources
- ETHUSDT: PASS; 43824 economic hours; 5478 official funding events; 744 warmup hours; 0 exact official daily market gapfill hours; error none.
- SOLUSDT: PASS; 43824 economic hours; 5553 official funding events; 744 warmup hours; 120 exact official daily market gapfill hours; error none.
- BNBUSDT: PASS; 43824 economic hours; 5478 official funding events; 744 warmup hours; 0 exact official daily market gapfill hours; error none.
Official Binance USD-M historical proxy, December 2020 warmup and 2021�2025 economic window. Downloaded official ZIP CHECKSUM verification inherited. No imputation, source substitution or 2026 data. This is not MEXC historical execution reconstruction.

## Shared 500-USDT account
| Metric | BASE | STRESS |
|---|---:|---:|
| Final balance USDT | 532.591965 | 515.952360 |
| Net USDT | 32.591965 | 15.952360 |
| Net return % | 6.518393 | 3.190472 |
| Trades | 459.000000 | 462.000000 |
| Win rate % | 22.657952 | 22.294372 |
| Net PF | 1.083100 | 1.039936 |
| Realized payoff | 3.697120 | 3.624631 |
| Close-based MTM DD % | -6.647089 | -6.943952 |
| Fees USDT | 19.079008 | 19.151921 |
| Funding cashflow USDT | -12.021789 | -11.906378 |
| Slippage USDT | 4.769755 | 11.969965 |
| Net excluding top1 USDT | 27.164126 | 10.590087 |
| Top1 share of positive PnL % | 1.277760 | 1.290863 |
| Top3 share of positive PnL % | 3.821765 | 3.828248 |
| Net excluding top3 USDT | 16.357360 | 0.049739 |
| Longest loss streak | 22.000000 | 22.000000 |
| Rejected opportunities | 52.000000 | 49.000000 |

BASE exit reasons: {"TARGET": 102, "STOP": 354, "FORCED_END": 3}. STRESS: {"TARGET": 101, "STOP": 358, "FORCED_END": 3}.

## Per-symbol shared-account attribution
Contributions below are not returns on independent 500-USDT accounts.
| Symbol | BASE trades | BASE net USDT | BASE win % | BASE PF | BASE payoff | STRESS trades | STRESS net USDT | STRESS PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ETHUSDT | 140 | 5.933243 | 22.857143 | 1.046478 | 3.531862 | 141 | 3.797283 | 1.029512 |
| SOLUSDT | 187 | 14.585819 | 22.459893 | 1.094794 | 3.779645 | 188 | 5.061763 | 1.031330 |
| BNBUSDT | 132 | 12.072904 | 22.727273 | 1.109085 | 3.770889 | 133 | 7.093314 | 1.064948 |

## Calendar years (exit-year attribution)
| Year | BASE net USDT | STRESS net USDT |
|---|---:|---:|
| 2021 | 11.076924 | 8.513878 |
| 2022 | -11.441159 | -11.910083 |
| 2023 | 22.054512 | 21.291075 |
| 2024 | 10.434182 | 3.277931 |
| 2025 | 0.467506 | -5.220441 |

## Inherited risk diagnostics
| Entry risk / aggregate cap | BASE final | STRESS final | BASE return % | STRESS return % |
|---|---:|---:|---:|---:|
| 0.25% / 0.5% | 532.591965 | 515.952360 | 6.518393 | 3.190472 |
| 0.5% / 1.0% | 559.449263 | 525.322229 | 11.889853 | 5.064446 |
| 1.0% / 2.0% | 592.775764 | 523.757772 | 18.555153 | 4.751554 |

## Frozen adjudication
{"BASE_PF_gt1": true, "BASE_net_excluding_top1_positive": true, "BASE_net_positive": true, "BASE_realized_payoff_ge4": false, "STRESS_PF_gt1": true, "STRESS_net_positive": true, "three_positive_symbols": true}
**HISTORICAL_DIAGNOSTIC_FAIL**. No threshold changed after outcomes. The realized-payoff hurdle is descriptive; economic net/PF findings are also reported separately.

## Parent comparison and feasibility
Original Parent V5 ETH/SOL/BNB BASE returns +96.12%, +91.23%, +255.84%, PF 1.212/1.141/1.266; STRESS returns +89.18%, +92.52%, +229.23%. It used separate initial 10000-USDT accounts, 95% allocation, 10bps fees per side and non-latched +5% activation/12% trailing. Its original local gate survived; later cross-section expansion failed. The present fixed 4R replay uses different exit state, 60-day timer, 8bps fees, shared 500-USDT capital and .25%/.5% planned risk caps. These are not equivalent economies; the aggregate difference is not an isolated causal estimate of changing the exit.
Fixed 4R caps fee-only winners at approximately +16.80064% price, whereas trailing retains trend tails and changes future eligible entries through position state. Full cost realized payoff can fall below 4.
Modeled account: full 1x collateral and aggregate planned risk constraints inherited, fractional quantities and no deposits. This demonstrates only research-model capital continuity. Historical MEXC minimum lots, fee tier, bid/ask depth, maintenance tiers, intrabar liquidation and actual fills are unverified. No leverage-specific feasibility conclusion. MTM DD is completed-bar-close based and can understate intrabar loss. Gaps can exceed planned risk.
2021�2025 was already exposed in the Parent; this is outcome-informed historical diagnosis, not independent family OOS. No selection of winning symbols, retuning, promotion, real trading, orders, private APIs, wallets, spending, Render, main mutation/merge or protected 2026 access.
Full source metadata, all six-arm ledgers and independently derived per-symbol costs/concentration are preserved in report.json and INDEPENDENT_AUDIT.json.

Artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38294457980/artifacts/11767976069
