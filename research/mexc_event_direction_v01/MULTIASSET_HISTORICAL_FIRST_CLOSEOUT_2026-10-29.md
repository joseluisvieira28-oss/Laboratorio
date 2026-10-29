# MEXC Event Futures multiasset: FIRST HISTORICAL DISCOVERY CLOSEOUT
Date 2026-10-29. Work: dedicated research PR for frozen 80-cell Oct22/23 study. NO LIVE / NO CERTIFIED EDGE.

## Evidence
- Previous exact public product capture [run 40897851853](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40897851853), SHA256 product source 662bd671f0cba970963eba6ee2ce86388ab7f0455638f7eeca7ec5d6432bace7. Recorded Oct29 15:04:53 UTC. Event Futures NVIDIA_USDT, SPCXSTOCK_USDT, MUSTOCK_USDT all ONLINE and displayed q=0.80 for 10m and q=0.85 for 30m, symmetrically UP/DOWN. These q are only contemporaneous 29 Oct NOT historical payout q on 22/23 Oct. Screenshot MLIUSDT is NOT authoritatively mapped to MUSTOCK, so MLI was NOT TESTED.
- Source-only previous run verified 576/576 MEXC standard Futures index Min5 bars each for BTC, ETH, NVIDIA, SPCXSTOCK, MUSTOCK from 2026-10-22T00Z through 2026-10-24T00Z. Raw source hashes frozen before outcomes.
- This frozen price-only diagnostic [run 40898314032](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40898314032), job 123533389816, head SHA 83c5353619f0301424d42aa842f6fc298f0622c7, artifact id 12908301446, artifact digest sha256:62680ce6de2b4287634b0d434a80b0c28b2fd6f2b4515d27a8acee4ad5702c82.
- Frozen rules UP_ALWAYS, DOWN_ALWAYS, ROC3_CONT, ROC3_REV; H=10/30m; ALL_24H and illustrative US_REGULAR_PROXY 13:30–20:00UTC (Oct22/23 US DST). Matched nonoverlapping decisions per cell. Note US subset overlaps 24H, so cells are NOT independent.
- 5 assets x4 rules x2 horizons x2 time strata = **80 cells**, source hashes and 576-bar integrity checks all passed; 0 source violations.
- **15/80 theoretical cells EV>0 at q=0.80 and 19/80 at q=0.85**. These are historical theoretical fixed-payout PROXIES, not historical MEXC Event Futures PnL.
- No per-cell statistical survivors were declared. Extremely small two-day window, multiple correlated cells, conditional session/market trend, unknown Event Futures product historical state/payout, index OPEN(t) != proven server-locked contract openPrice/settlement.
- For 30m 24H: NVDA DOWN_ALWAYS 53W/40L/2T of N95 (56.99% ex ties, q80 EV +0.02526), SPCXSTOCK ROC3_REV 51W/39L/1T of N91 (56.67%, +0.01978), MU DOWN_ALWAYS 55W/40L/0T N95 (57.89%, +0.04211); these post-view examples are NOT evidence of an independent viable rule.
- MU US_REGULAR_PROXY DOWN_ALWAYS 18W/8L N26 (69.23% / illustrative EV +0.24615); both calendar days gave 9W/4L but n13/day is tiny and this cell was identified among 80 overlapping comparisons. **NOT ELIGIBLE FOR PROMOTION**, do not tune/extend only this winner.
- Other 30m price-only BTC DOWN_ALWAYS also 58W/37L N95 (+0.09895 at q80); this exposes a shared price downtrend across assets, not new transferable structural alpha.
- All 22/23 historical bars were opened only after the exact frozen study code committed. Not a protected independent OOS; no September 2026 holdout opened. No authorisation for trading.

## Complete results
| Símbolo | H | Regra | Estrato | N | Win | Loss | Tie | Acerto | EV 0.80 | EV 0.85 |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| BTC_USDT | 10m | UP_ALWAYS | ALL_24H | 287 | 137 | 150 | 0 | 47.74% | -0.14077 | -0.11690 |
| BTC_USDT | 10m | UP_ALWAYS | US_REGULAR_PROXY | 78 | 38 | 40 | 0 | 48.72% | -0.12308 | -0.09872 |
| BTC_USDT | 10m | DOWN_ALWAYS | ALL_24H | 287 | 150 | 137 | 0 | 52.26% | -0.05923 | -0.03310 |
| BTC_USDT | 10m | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 40 | 38 | 0 | 51.28% | -0.07692 | -0.05128 |
| BTC_USDT | 10m | ROC3_CONT | ALL_24H | 285 | 129 | 156 | 0 | 45.26% | -0.18526 | -0.16263 |
| BTC_USDT | 10m | ROC3_CONT | US_REGULAR_PROXY | 78 | 38 | 40 | 0 | 48.72% | -0.12308 | -0.09872 |
| BTC_USDT | 10m | ROC3_REV | ALL_24H | 285 | 156 | 129 | 0 | 54.74% | -0.01474 | 0.01263 |
| BTC_USDT | 10m | ROC3_REV | US_REGULAR_PROXY | 78 | 40 | 38 | 0 | 51.28% | -0.07692 | -0.05128 |
| BTC_USDT | 30m | UP_ALWAYS | ALL_24H | 95 | 37 | 58 | 0 | 38.95% | -0.29895 | -0.27947 |
| BTC_USDT | 30m | UP_ALWAYS | US_REGULAR_PROXY | 26 | 11 | 15 | 0 | 42.31% | -0.23846 | -0.21731 |
| BTC_USDT | 30m | DOWN_ALWAYS | ALL_24H | 95 | 58 | 37 | 0 | 61.05% | 0.09895 | 0.12947 |
| BTC_USDT | 30m | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 15 | 11 | 0 | 57.69% | 0.03846 | 0.06731 |
| BTC_USDT | 30m | ROC3_CONT | ALL_24H | 94 | 47 | 47 | 0 | 50.00% | -0.10000 | -0.07500 |
| BTC_USDT | 30m | ROC3_CONT | US_REGULAR_PROXY | 26 | 15 | 11 | 0 | 57.69% | 0.03846 | 0.06731 |
| BTC_USDT | 30m | ROC3_REV | ALL_24H | 94 | 47 | 47 | 0 | 50.00% | -0.10000 | -0.07500 |
| BTC_USDT | 30m | ROC3_REV | US_REGULAR_PROXY | 26 | 11 | 15 | 0 | 42.31% | -0.23846 | -0.21731 |
| ETH_USDT | 10m | UP_ALWAYS | ALL_24H | 287 | 141 | 146 | 0 | 49.13% | -0.11568 | -0.09111 |
| ETH_USDT | 10m | UP_ALWAYS | US_REGULAR_PROXY | 78 | 36 | 42 | 0 | 46.15% | -0.16923 | -0.14615 |
| ETH_USDT | 10m | DOWN_ALWAYS | ALL_24H | 287 | 146 | 141 | 0 | 50.87% | -0.08432 | -0.05889 |
| ETH_USDT | 10m | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 42 | 36 | 0 | 53.85% | -0.03077 | -0.00385 |
| ETH_USDT | 10m | ROC3_CONT | ALL_24H | 285 | 124 | 161 | 0 | 43.51% | -0.21684 | -0.19509 |
| ETH_USDT | 10m | ROC3_CONT | US_REGULAR_PROXY | 78 | 35 | 43 | 0 | 44.87% | -0.19231 | -0.16987 |
| ETH_USDT | 10m | ROC3_REV | ALL_24H | 285 | 161 | 124 | 0 | 56.49% | 0.01684 | 0.04509 |
| ETH_USDT | 10m | ROC3_REV | US_REGULAR_PROXY | 78 | 43 | 35 | 0 | 55.13% | -0.00769 | 0.01987 |
| ETH_USDT | 30m | UP_ALWAYS | ALL_24H | 95 | 42 | 53 | 0 | 44.21% | -0.20421 | -0.18211 |
| ETH_USDT | 30m | UP_ALWAYS | US_REGULAR_PROXY | 26 | 12 | 14 | 0 | 46.15% | -0.16923 | -0.14615 |
| ETH_USDT | 30m | DOWN_ALWAYS | ALL_24H | 95 | 53 | 42 | 0 | 55.79% | 0.00421 | 0.03211 |
| ETH_USDT | 30m | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 14 | 12 | 0 | 53.85% | -0.03077 | -0.00385 |
| ETH_USDT | 30m | ROC3_CONT | ALL_24H | 94 | 41 | 53 | 0 | 43.62% | -0.21489 | -0.19309 |
| ETH_USDT | 30m | ROC3_CONT | US_REGULAR_PROXY | 26 | 14 | 12 | 0 | 53.85% | -0.03077 | -0.00385 |
| ETH_USDT | 30m | ROC3_REV | ALL_24H | 94 | 53 | 41 | 0 | 56.38% | 0.01489 | 0.04309 |
| ETH_USDT | 30m | ROC3_REV | US_REGULAR_PROXY | 26 | 12 | 14 | 0 | 46.15% | -0.16923 | -0.14615 |
| NVIDIA_USDT | 10m | UP_ALWAYS | ALL_24H | 287 | 131 | 150 | 6 | 46.62% | -0.15749 | -0.13467 |
| NVIDIA_USDT | 10m | UP_ALWAYS | US_REGULAR_PROXY | 78 | 35 | 42 | 1 | 45.45% | -0.17949 | -0.15705 |
| NVIDIA_USDT | 10m | DOWN_ALWAYS | ALL_24H | 287 | 150 | 131 | 6 | 53.38% | -0.03833 | -0.01220 |
| NVIDIA_USDT | 10m | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 42 | 35 | 1 | 54.55% | -0.01795 | 0.00897 |
| NVIDIA_USDT | 10m | ROC3_CONT | ALL_24H | 283 | 141 | 136 | 6 | 50.90% | -0.08198 | -0.05707 |
| NVIDIA_USDT | 10m | ROC3_CONT | US_REGULAR_PROXY | 78 | 39 | 38 | 1 | 50.65% | -0.08718 | -0.06218 |
| NVIDIA_USDT | 10m | ROC3_REV | ALL_24H | 283 | 136 | 141 | 6 | 49.10% | -0.11378 | -0.08975 |
| NVIDIA_USDT | 10m | ROC3_REV | US_REGULAR_PROXY | 78 | 38 | 39 | 1 | 49.35% | -0.11026 | -0.08590 |
| NVIDIA_USDT | 30m | UP_ALWAYS | ALL_24H | 95 | 40 | 53 | 2 | 43.01% | -0.22105 | -0.20000 |
| NVIDIA_USDT | 30m | UP_ALWAYS | US_REGULAR_PROXY | 26 | 10 | 14 | 2 | 41.67% | -0.23077 | -0.21154 |
| NVIDIA_USDT | 30m | DOWN_ALWAYS | ALL_24H | 95 | 53 | 40 | 2 | 56.99% | 0.02526 | 0.05316 |
| NVIDIA_USDT | 30m | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 14 | 10 | 2 | 58.33% | 0.04615 | 0.07308 |
| NVIDIA_USDT | 30m | ROC3_CONT | ALL_24H | 94 | 46 | 46 | 2 | 50.00% | -0.09787 | -0.07340 |
| NVIDIA_USDT | 30m | ROC3_CONT | US_REGULAR_PROXY | 26 | 9 | 15 | 2 | 37.50% | -0.30000 | -0.28269 |
| NVIDIA_USDT | 30m | ROC3_REV | ALL_24H | 94 | 46 | 46 | 2 | 50.00% | -0.09787 | -0.07340 |
| NVIDIA_USDT | 30m | ROC3_REV | US_REGULAR_PROXY | 26 | 15 | 9 | 2 | 62.50% | 0.11538 | 0.14423 |
| SPCXSTOCK_USDT | 10m | UP_ALWAYS | ALL_24H | 287 | 133 | 154 | 0 | 46.34% | -0.16585 | -0.14268 |
| SPCXSTOCK_USDT | 10m | UP_ALWAYS | US_REGULAR_PROXY | 78 | 31 | 47 | 0 | 39.74% | -0.28462 | -0.26474 |
| SPCXSTOCK_USDT | 10m | DOWN_ALWAYS | ALL_24H | 287 | 154 | 133 | 0 | 53.66% | -0.03415 | -0.00732 |
| SPCXSTOCK_USDT | 10m | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 47 | 31 | 0 | 60.26% | 0.08462 | 0.11474 |
| SPCXSTOCK_USDT | 10m | ROC3_CONT | ALL_24H | 280 | 128 | 152 | 0 | 45.71% | -0.17714 | -0.15429 |
| SPCXSTOCK_USDT | 10m | ROC3_CONT | US_REGULAR_PROXY | 77 | 37 | 40 | 0 | 48.05% | -0.13506 | -0.11104 |
| SPCXSTOCK_USDT | 10m | ROC3_REV | ALL_24H | 280 | 152 | 128 | 0 | 54.29% | -0.02286 | 0.00429 |
| SPCXSTOCK_USDT | 10m | ROC3_REV | US_REGULAR_PROXY | 77 | 40 | 37 | 0 | 51.95% | -0.06494 | -0.03896 |
| SPCXSTOCK_USDT | 30m | UP_ALWAYS | ALL_24H | 95 | 44 | 50 | 1 | 46.81% | -0.15579 | -0.13263 |
| SPCXSTOCK_USDT | 30m | UP_ALWAYS | US_REGULAR_PROXY | 26 | 10 | 16 | 0 | 38.46% | -0.30769 | -0.28846 |
| SPCXSTOCK_USDT | 30m | DOWN_ALWAYS | ALL_24H | 95 | 50 | 44 | 1 | 53.19% | -0.04211 | -0.01579 |
| SPCXSTOCK_USDT | 30m | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 16 | 10 | 0 | 61.54% | 0.10769 | 0.13846 |
| SPCXSTOCK_USDT | 30m | ROC3_CONT | ALL_24H | 91 | 39 | 51 | 1 | 43.33% | -0.21758 | -0.19615 |
| SPCXSTOCK_USDT | 30m | ROC3_CONT | US_REGULAR_PROXY | 25 | 13 | 12 | 0 | 52.00% | -0.06400 | -0.03800 |
| SPCXSTOCK_USDT | 30m | ROC3_REV | ALL_24H | 91 | 51 | 39 | 1 | 56.67% | 0.01978 | 0.04780 |
| SPCXSTOCK_USDT | 30m | ROC3_REV | US_REGULAR_PROXY | 25 | 12 | 13 | 0 | 48.00% | -0.13600 | -0.11200 |
| MUSTOCK_USDT | 10m | UP_ALWAYS | ALL_24H | 287 | 142 | 145 | 0 | 49.48% | -0.10941 | -0.08467 |
| MUSTOCK_USDT | 10m | UP_ALWAYS | US_REGULAR_PROXY | 78 | 39 | 39 | 0 | 50.00% | -0.10000 | -0.07500 |
| MUSTOCK_USDT | 10m | DOWN_ALWAYS | ALL_24H | 287 | 145 | 142 | 0 | 50.52% | -0.09059 | -0.06533 |
| MUSTOCK_USDT | 10m | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 39 | 39 | 0 | 50.00% | -0.10000 | -0.07500 |
| MUSTOCK_USDT | 10m | ROC3_CONT | ALL_24H | 284 | 150 | 134 | 0 | 52.82% | -0.04930 | -0.02289 |
| MUSTOCK_USDT | 10m | ROC3_CONT | US_REGULAR_PROXY | 78 | 40 | 38 | 0 | 51.28% | -0.07692 | -0.05128 |
| MUSTOCK_USDT | 10m | ROC3_REV | ALL_24H | 284 | 134 | 150 | 0 | 47.18% | -0.15070 | -0.12711 |
| MUSTOCK_USDT | 10m | ROC3_REV | US_REGULAR_PROXY | 78 | 38 | 40 | 0 | 48.72% | -0.12308 | -0.09872 |
| MUSTOCK_USDT | 30m | UP_ALWAYS | ALL_24H | 95 | 40 | 55 | 0 | 42.11% | -0.24211 | -0.22105 |
| MUSTOCK_USDT | 30m | UP_ALWAYS | US_REGULAR_PROXY | 26 | 8 | 18 | 0 | 30.77% | -0.44615 | -0.43077 |
| MUSTOCK_USDT | 30m | DOWN_ALWAYS | ALL_24H | 95 | 55 | 40 | 0 | 57.89% | 0.04211 | 0.07105 |
| MUSTOCK_USDT | 30m | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 18 | 8 | 0 | 69.23% | 0.24615 | 0.28077 |
| MUSTOCK_USDT | 30m | ROC3_CONT | ALL_24H | 93 | 49 | 44 | 0 | 52.69% | -0.05161 | -0.02527 |
| MUSTOCK_USDT | 30m | ROC3_CONT | US_REGULAR_PROXY | 26 | 15 | 11 | 0 | 57.69% | 0.03846 | 0.06731 |
| MUSTOCK_USDT | 30m | ROC3_REV | ALL_24H | 93 | 44 | 49 | 0 | 47.31% | -0.14839 | -0.12473 |
| MUSTOCK_USDT | 30m | ROC3_REV | US_REGULAR_PROXY | 26 | 11 | 15 | 0 | 42.31% | -0.23846 | -0.21731 |

## Verdict
**HISTORICAL_DISCOVERY_ONLY / SOME_POSITIVE_HYPOTHETICAL_CELLS / NO_INDEPENDENT_ECONOMIC_EDGE / NO_LIVE_GO**.

Before forward: prospective payout q per side/horizon, exact public indexed shadow tick, product online/schedule observation, real timestamp-anchored feature receipt, frozen model, robust time/OOS splitting and baseline/ablation with multiplicity. If historical replication follows, apply ALL 80 frozen cells unchanged to future/date separately with a fresh source freeze (including America/New_York DST); do not selectively rescue good cells. The old Triple Flow V0.2 source-continuity failure remains untouched; no feed-based Triple Flow rule was applied to stock assets.

No accounts, private endpoints, orders, money, main merges or live trading.
