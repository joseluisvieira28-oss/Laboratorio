# Event Futures Multiasset V0.3 — ALL-CELL HISTORICAL REPLICATION CLOSEOUT
Date: 2026-10-29. Historical price-only diagnostics, no live trading or actual Event Futures payout.

## Proof and version authority
- Parent 22/23 Oct fixed source+80-cell exploratory run [40898314032](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40898314032); job 123533389816; artifact id 12908301446, digest sha256:62680ce6de2b4287634b0d434a80b0c28b2fd6f2b4515d27a8acee4ad5702c82. Science frozen before directional outcomes; results in MULTIASSET_HISTORICAL_FIRST_CLOSEOUT_2026-10-29.md.
- Replication pre-freeze commit a3af5357357f64a62fda18aa1699f3e5f9c87d06; **first replication run [40899093330](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40899093330) failed before any price-source GET** due an incorrect synthetic assertion claiming US DST ended Oct25, when US DST ends Nov1. The function already used IANA America/New_York correctly. Only the assertion was fixed and a separate immutable pre-outcome errata committed at 523975ff9d4f0619d9fc6f2d5f152db49b911fc5. No feature/strategy/science/date/payout gate changed; the failed run has zero outcome evaluation.
- Authoritative replication [run 40899287495](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40899287495), job 123536838646, head 523975ff9d4f0619d9fc6f2d5f152db49b911fc5, artifact id 12909270074, artifact digest sha256:87ba273e904bd6c3808f05e10b642a898c15e3734d55acf1b352da1ca3fc086c. SOURCE_GRID_PASS: 576/576 valid public MEXC standard Futures index open Min5 for all five exact internal symbols, Oct26/27.
- Oct22/23 and Oct26/27 (two windows, 4 calendar days total) each evaluate exactly same 80 cells: 5 assets x 2 horizons (10/30m) x 4 unmodified price rules x 2 overlapping strata ALL_24H / US_REGULAR_PROXY. The latter is illustrative 09:30-16:00 America/New_York; BOTH windows are EDT UTC-4 and 13:30–20:00 UTC in 2026. Session is not proven Event Futures eligibility schedule.
- No MEXC Event Futures historical payouts/entry/expiry receipts are recovered. Payout scenarios q=0.40,0.70,0.80,0.85 symmetric and hypothetical; no executed PnL.

## Summary
- First window: **15/80** cells positive hypothetical EV q=0.80.
- Replication window: **17/80** cells positive hypothetical EV q=0.80.
- Both windows positive in only **3/80** cells. The session and 24h cells share outcomes and tests are highly correlated; counts do not imply 80 independent trials or posterior evidence of edge.
- The strongest highlighted first-window MU US_REGULAR_PROXY 30m DOWN_ALWAYS fell from 18W/8L out of N26 (69.23%) to 12W/14L out of N26 (46.15%) in second window. NVDA ALL_24H 30m DOWN_ALWAYS fell from 53W/40L/2T (56.99% excl ties) to 39W/55L/1T (41.49%).
- Surviving-positive examples q80 (EX POST descriptions, NOT survivor status):
  - BTC_USDT|30|ROC3_CONT|US_REGULAR_PROXY: first 15W/11L/0T (N26, EV 0.03846) and replica 15W/11L/0T (N26, EV 0.03846).
  - SPCXSTOCK_USDT|30|DOWN_ALWAYS|US_REGULAR_PROXY: first 16W/10L/0T (N26, EV 0.10769) and replica 16W/10L/0T (N26, EV 0.10769).
  - MUSTOCK_USDT|30|ROC3_CONT|US_REGULAR_PROXY: first 15W/11L/0T (N26, EV 0.03846) and replica 15W/11L/0T (N26, EV 0.03846).
- In particular SPCXSTOCK_USDT 30m DOWN_ALWAYS during US_REGULAR_PROXY: 16W/10L out of 26 in each two-day window (total 32/52, observed 61.54% excluding ties). Under a hypothetical fixed q=0.80 break-even probability 55.56%, unadjusted one-sided exact binomial tail p approximately **0.2340** for 32/52, far above alpha 0.05 even WITHOUT correcting the many comparisons. Not statistically certified, not execution/payout certified.
- The Oct26/27 validation was frozen before reading its price source, but it is still only an available historical replay. No independent protected holdout or forward evidence; September 2026 sealed holdout remains untouched.
- The screenshot label MLIUSDT was never authoritatively mapped. MUSTOCK_USDT was tested as a separate verified MEXC product, **not** asserted identical to MLI. Exact current Event Futures stock payout 80%/85% as-of Oct29 was observed but NOT bound to either historical window.
- Historical observations using 5min OPEN prices are only an index proxy; source/market execution price parity, payout time sequence and availability, position eligibility, forecasting ability and reliable net EV remain UNPROVEN.

## First versus second: all 80 frozen cells (unit EV q=0.80 only)
| Symbol | H min | Rule | Stratum | N1 | W/L/T1 | EV1 | N2 | W/L/T2 | EV2 |
|---|---:|---|---|---:|---|---:|---:|---|---:|
| BTC_USDT | 10 | UP_ALWAYS | ALL_24H | 287 | 137/150/0 | -0.14077 | 287 | 145/142/0 | -0.09059 |
| BTC_USDT | 10 | UP_ALWAYS | US_REGULAR_PROXY | 78 | 38/40/0 | -0.12308 | 78 | 45/33/0 | 0.03846 |
| BTC_USDT | 10 | DOWN_ALWAYS | ALL_24H | 287 | 150/137/0 | -0.05923 | 287 | 142/145/0 | -0.10941 |
| BTC_USDT | 10 | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 40/38/0 | -0.07692 | 78 | 33/45/0 | -0.23846 |
| BTC_USDT | 10 | ROC3_CONT | ALL_24H | 285 | 129/156/0 | -0.18526 | 285 | 127/158/0 | -0.19789 |
| BTC_USDT | 10 | ROC3_CONT | US_REGULAR_PROXY | 78 | 38/40/0 | -0.12308 | 78 | 36/42/0 | -0.16923 |
| BTC_USDT | 10 | ROC3_REV | ALL_24H | 285 | 156/129/0 | -0.01474 | 285 | 158/127/0 | -0.00211 |
| BTC_USDT | 10 | ROC3_REV | US_REGULAR_PROXY | 78 | 40/38/0 | -0.07692 | 78 | 42/36/0 | -0.03077 |
| BTC_USDT | 30 | UP_ALWAYS | ALL_24H | 95 | 37/58/0 | -0.29895 | 95 | 54/41/0 | 0.02316 |
| BTC_USDT | 30 | UP_ALWAYS | US_REGULAR_PROXY | 26 | 11/15/0 | -0.23846 | 26 | 17/9/0 | 0.17692 |
| BTC_USDT | 30 | DOWN_ALWAYS | ALL_24H | 95 | 58/37/0 | 0.09895 | 95 | 41/54/0 | -0.22316 |
| BTC_USDT | 30 | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 15/11/0 | 0.03846 | 26 | 9/17/0 | -0.37692 |
| BTC_USDT | 30 | ROC3_CONT | ALL_24H | 94 | 47/47/0 | -0.10000 | 94 | 53/41/0 | 0.01489 |
| BTC_USDT | 30 | ROC3_CONT | US_REGULAR_PROXY | 26 | 15/11/0 | 0.03846 | 26 | 15/11/0 | 0.03846 |
| BTC_USDT | 30 | ROC3_REV | ALL_24H | 94 | 47/47/0 | -0.10000 | 94 | 41/53/0 | -0.21489 |
| BTC_USDT | 30 | ROC3_REV | US_REGULAR_PROXY | 26 | 11/15/0 | -0.23846 | 26 | 11/15/0 | -0.23846 |
| ETH_USDT | 10 | UP_ALWAYS | ALL_24H | 287 | 141/146/0 | -0.11568 | 287 | 139/148/0 | -0.12822 |
| ETH_USDT | 10 | UP_ALWAYS | US_REGULAR_PROXY | 78 | 36/42/0 | -0.16923 | 78 | 40/38/0 | -0.07692 |
| ETH_USDT | 10 | DOWN_ALWAYS | ALL_24H | 287 | 146/141/0 | -0.08432 | 287 | 148/139/0 | -0.07178 |
| ETH_USDT | 10 | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 42/36/0 | -0.03077 | 78 | 38/40/0 | -0.12308 |
| ETH_USDT | 10 | ROC3_CONT | ALL_24H | 285 | 124/161/0 | -0.21684 | 283 | 128/155/0 | -0.18587 |
| ETH_USDT | 10 | ROC3_CONT | US_REGULAR_PROXY | 78 | 35/43/0 | -0.19231 | 77 | 34/43/0 | -0.20519 |
| ETH_USDT | 10 | ROC3_REV | ALL_24H | 285 | 161/124/0 | 0.01684 | 283 | 155/128/0 | -0.01413 |
| ETH_USDT | 10 | ROC3_REV | US_REGULAR_PROXY | 78 | 43/35/0 | -0.00769 | 77 | 43/34/0 | 0.00519 |
| ETH_USDT | 30 | UP_ALWAYS | ALL_24H | 95 | 42/53/0 | -0.20421 | 95 | 51/44/0 | -0.03368 |
| ETH_USDT | 30 | UP_ALWAYS | US_REGULAR_PROXY | 26 | 12/14/0 | -0.16923 | 26 | 17/9/0 | 0.17692 |
| ETH_USDT | 30 | DOWN_ALWAYS | ALL_24H | 95 | 53/42/0 | 0.00421 | 95 | 44/51/0 | -0.16632 |
| ETH_USDT | 30 | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 14/12/0 | -0.03077 | 26 | 9/17/0 | -0.37692 |
| ETH_USDT | 30 | ROC3_CONT | ALL_24H | 94 | 41/53/0 | -0.21489 | 94 | 48/46/0 | -0.08085 |
| ETH_USDT | 30 | ROC3_CONT | US_REGULAR_PROXY | 26 | 14/12/0 | -0.03077 | 26 | 12/14/0 | -0.16923 |
| ETH_USDT | 30 | ROC3_REV | ALL_24H | 94 | 53/41/0 | 0.01489 | 94 | 46/48/0 | -0.11915 |
| ETH_USDT | 30 | ROC3_REV | US_REGULAR_PROXY | 26 | 12/14/0 | -0.16923 | 26 | 14/12/0 | -0.03077 |
| NVIDIA_USDT | 10 | UP_ALWAYS | ALL_24H | 287 | 131/150/6 | -0.15749 | 287 | 137/142/8 | -0.11289 |
| NVIDIA_USDT | 10 | UP_ALWAYS | US_REGULAR_PROXY | 78 | 35/42/1 | -0.17949 | 78 | 36/39/3 | -0.13077 |
| NVIDIA_USDT | 10 | DOWN_ALWAYS | ALL_24H | 287 | 150/131/6 | -0.03833 | 287 | 142/137/8 | -0.08153 |
| NVIDIA_USDT | 10 | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 42/35/1 | -0.01795 | 78 | 39/36/3 | -0.06154 |
| NVIDIA_USDT | 10 | ROC3_CONT | ALL_24H | 283 | 141/136/6 | -0.08198 | 278 | 137/134/7 | -0.08777 |
| NVIDIA_USDT | 10 | ROC3_CONT | US_REGULAR_PROXY | 78 | 39/38/1 | -0.08718 | 77 | 32/42/3 | -0.21299 |
| NVIDIA_USDT | 10 | ROC3_REV | ALL_24H | 283 | 136/141/6 | -0.11378 | 278 | 134/137/7 | -0.10719 |
| NVIDIA_USDT | 10 | ROC3_REV | US_REGULAR_PROXY | 78 | 38/39/1 | -0.11026 | 77 | 42/32/3 | 0.02078 |
| NVIDIA_USDT | 30 | UP_ALWAYS | ALL_24H | 95 | 40/53/2 | -0.22105 | 95 | 55/39/1 | 0.05263 |
| NVIDIA_USDT | 30 | UP_ALWAYS | US_REGULAR_PROXY | 26 | 10/14/2 | -0.23077 | 26 | 16/10/0 | 0.10769 |
| NVIDIA_USDT | 30 | DOWN_ALWAYS | ALL_24H | 95 | 53/40/2 | 0.02526 | 95 | 39/55/1 | -0.25053 |
| NVIDIA_USDT | 30 | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 14/10/2 | 0.04615 | 26 | 10/16/0 | -0.30769 |
| NVIDIA_USDT | 30 | ROC3_CONT | ALL_24H | 94 | 46/46/2 | -0.09787 | 93 | 55/37/1 | 0.07527 |
| NVIDIA_USDT | 30 | ROC3_CONT | US_REGULAR_PROXY | 26 | 9/15/2 | -0.30000 | 26 | 12/14/0 | -0.16923 |
| NVIDIA_USDT | 30 | ROC3_REV | ALL_24H | 94 | 46/46/2 | -0.09787 | 93 | 37/55/1 | -0.27312 |
| NVIDIA_USDT | 30 | ROC3_REV | US_REGULAR_PROXY | 26 | 15/9/2 | 0.11538 | 26 | 14/12/0 | -0.03077 |
| SPCXSTOCK_USDT | 10 | UP_ALWAYS | ALL_24H | 287 | 133/154/0 | -0.16585 | 287 | 141/144/2 | -0.10871 |
| SPCXSTOCK_USDT | 10 | UP_ALWAYS | US_REGULAR_PROXY | 78 | 31/47/0 | -0.28462 | 78 | 40/38/0 | -0.07692 |
| SPCXSTOCK_USDT | 10 | DOWN_ALWAYS | ALL_24H | 287 | 154/133/0 | -0.03415 | 287 | 144/141/2 | -0.08990 |
| SPCXSTOCK_USDT | 10 | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 47/31/0 | 0.08462 | 78 | 38/40/0 | -0.12308 |
| SPCXSTOCK_USDT | 10 | ROC3_CONT | ALL_24H | 280 | 128/152/0 | -0.17714 | 277 | 131/144/2 | -0.14152 |
| SPCXSTOCK_USDT | 10 | ROC3_CONT | US_REGULAR_PROXY | 77 | 37/40/0 | -0.13506 | 77 | 41/36/0 | -0.04156 |
| SPCXSTOCK_USDT | 10 | ROC3_REV | ALL_24H | 280 | 152/128/0 | -0.02286 | 277 | 144/131/2 | -0.05704 |
| SPCXSTOCK_USDT | 10 | ROC3_REV | US_REGULAR_PROXY | 77 | 40/37/0 | -0.06494 | 77 | 36/41/0 | -0.15844 |
| SPCXSTOCK_USDT | 30 | UP_ALWAYS | ALL_24H | 95 | 44/50/1 | -0.15579 | 95 | 46/48/1 | -0.11789 |
| SPCXSTOCK_USDT | 30 | UP_ALWAYS | US_REGULAR_PROXY | 26 | 10/16/0 | -0.30769 | 26 | 10/16/0 | -0.30769 |
| SPCXSTOCK_USDT | 30 | DOWN_ALWAYS | ALL_24H | 95 | 50/44/1 | -0.04211 | 95 | 48/46/1 | -0.08000 |
| SPCXSTOCK_USDT | 30 | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 16/10/0 | 0.10769 | 26 | 16/10/0 | 0.10769 |
| SPCXSTOCK_USDT | 30 | ROC3_CONT | ALL_24H | 91 | 39/51/1 | -0.21758 | 92 | 42/49/1 | -0.16739 |
| SPCXSTOCK_USDT | 30 | ROC3_CONT | US_REGULAR_PROXY | 25 | 13/12/0 | -0.06400 | 26 | 15/11/0 | 0.03846 |
| SPCXSTOCK_USDT | 30 | ROC3_REV | ALL_24H | 91 | 51/39/1 | 0.01978 | 92 | 49/42/1 | -0.03043 |
| SPCXSTOCK_USDT | 30 | ROC3_REV | US_REGULAR_PROXY | 25 | 12/13/0 | -0.13600 | 26 | 11/15/0 | -0.23846 |
| MUSTOCK_USDT | 10 | UP_ALWAYS | ALL_24H | 287 | 142/145/0 | -0.10941 | 287 | 151/133/3 | -0.04251 |
| MUSTOCK_USDT | 10 | UP_ALWAYS | US_REGULAR_PROXY | 78 | 39/39/0 | -0.10000 | 78 | 42/36/0 | -0.03077 |
| MUSTOCK_USDT | 10 | DOWN_ALWAYS | ALL_24H | 287 | 145/142/0 | -0.09059 | 287 | 133/151/3 | -0.15540 |
| MUSTOCK_USDT | 10 | DOWN_ALWAYS | US_REGULAR_PROXY | 78 | 39/39/0 | -0.10000 | 78 | 36/42/0 | -0.16923 |
| MUSTOCK_USDT | 10 | ROC3_CONT | ALL_24H | 284 | 150/134/0 | -0.04930 | 284 | 146/135/3 | -0.06408 |
| MUSTOCK_USDT | 10 | ROC3_CONT | US_REGULAR_PROXY | 78 | 40/38/0 | -0.07692 | 77 | 34/43/0 | -0.20519 |
| MUSTOCK_USDT | 10 | ROC3_REV | ALL_24H | 284 | 134/150/0 | -0.15070 | 284 | 135/146/3 | -0.13380 |
| MUSTOCK_USDT | 10 | ROC3_REV | US_REGULAR_PROXY | 78 | 38/40/0 | -0.12308 | 77 | 43/34/0 | 0.00519 |
| MUSTOCK_USDT | 30 | UP_ALWAYS | ALL_24H | 95 | 40/55/0 | -0.24211 | 95 | 53/42/0 | 0.00421 |
| MUSTOCK_USDT | 30 | UP_ALWAYS | US_REGULAR_PROXY | 26 | 8/18/0 | -0.44615 | 26 | 14/12/0 | -0.03077 |
| MUSTOCK_USDT | 30 | DOWN_ALWAYS | ALL_24H | 95 | 55/40/0 | 0.04211 | 95 | 42/53/0 | -0.20421 |
| MUSTOCK_USDT | 30 | DOWN_ALWAYS | US_REGULAR_PROXY | 26 | 18/8/0 | 0.24615 | 26 | 12/14/0 | -0.16923 |
| MUSTOCK_USDT | 30 | ROC3_CONT | ALL_24H | 93 | 49/44/0 | -0.05161 | 94 | 55/39/0 | 0.05319 |
| MUSTOCK_USDT | 30 | ROC3_CONT | US_REGULAR_PROXY | 26 | 15/11/0 | 0.03846 | 26 | 15/11/0 | 0.03846 |
| MUSTOCK_USDT | 30 | ROC3_REV | ALL_24H | 93 | 44/49/0 | -0.14839 | 94 | 39/55/0 | -0.25319 |
| MUSTOCK_USDT | 30 | ROC3_REV | US_REGULAR_PROXY | 26 | 11/15/0 | -0.23846 | 26 | 11/15/0 | -0.23846 |

## Replication raw source SHA256
| Symbol | 5m bars | SHA256 of raw public MEXC response |
|---|---:|---|
| BTC_USDT | 576 | `7ad6463221ed89071013d72a5ae37f87f43f639b0723a64b99d1226fb2556463` |
| ETH_USDT | 576 | `8be85637c7117cdc3ae92c77a6676868bcd92925323bd8c2f399c189e568e109` |
| NVIDIA_USDT | 576 | `e5bb2ded938bcb4abec82afe8937ef9ca0b504d8d55c930fc22d6ff8c377df05` |
| SPCXSTOCK_USDT | 576 | `93300ca3e0e05a2ae9c8257c79a02ff5e6947d52e2d394e6ce74e09075467c5d` |
| MUSTOCK_USDT | 576 | `723f910332773fe1ac31e6c9e32b11ab7c14c3ef6532eea3d4c23fa889327d73` |

## Final scientific verdict
**HISTORICAL_REPLICATION_COMPLETED / NO_INDEPENDENT_ECONOMIC_EDGE / NO_LIVE_GO**.

No strategy is promoted, selected for live action, auto-tuned or combined post-hoc to rescue positive cells. If more investigation is warranted, the next test should target a structurally different, pre-registered market mechanism (equity-index reference regime/stock opening auction and actual Event Futures payout+settlement point-in-time), not a repeat of static trend directions. No orders, API keys, account reads, private endpoints, wallets, spending, main changes/merge, September holdout or live trading.
