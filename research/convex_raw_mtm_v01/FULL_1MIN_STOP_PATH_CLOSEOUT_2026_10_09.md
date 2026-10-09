# BTC Convex Parent V5 — FULL 1-MINUTE STOP HISTORICAL SOURCE CLOSEOUT — 09 OCT 2026

## DECISION: FULL_1M_STOP_SOURCE_GATE_PASS — BUT NOT EXECUTABLE-FILL PROOF

- Original historical source ETH/SOL/BNB, already-opened 2021-01-01→2025-12-31 Parent V5, original canonical artifact `10775714534`; exact separate BASE and STRESS stop paths preserved.
- Canonical run GitHub Actions **37917719450**, conclusion **SUCCESS**, commit SHA **f51fcaef3ae87880c1912ed080cfd61f67660247**, artifact **11610061502** name `btc-convex-official-1minute-stop-gap-v01`.
- Official Binance USD-M futures monthly `1m` archives, pinned SHA256 receipts per downloaded ZIP and official CHECKSUM where available, exact daily official fallback only if missing full minute source; 60 unique 1m timestamps required for EVERY originally recorded exit hour. **No minute source was fabricated or interpolated.** This dataset is source-verification of original 1h exit bars, not independent new OOS.
- **BASE: 362/362 STOP hours confirmed by earliest 1m lower crossing; 3/3 FORCED_END original last-hour close confirmed.**
- **STRESS: 363/363 STOP hours confirmed by earliest 1m lower crossing; 3/3 FORCED_END original last-hour close confirmed.**
- Required missing or irreconcilable stop events: **0**. Full source gate PASS.
- If the first observed crossing minute began BELOW original raw 1h stop-fill reference, an extra adverse stop penalty was pre-frozen, but in this historical source: **0 qualifying minute-open-below-stop penalty events, max additional minute-open gap cost = 0bps** for both cost layers. This means no *additional modeled minute-open penalty*; it DOES NOT show true slippage/gaps inside the crossing minute, and DOES NOT prove a fill at the stop price.
- Recompounded original shared-capital portfolio using the fixed 0.25% / 0.50% risk budgets, max 1% planned aggregate risk, original BASE/STRESS fees and funding. Because no extra observed minute-open penalties, the conditional stress PnL did not change from original.

| Full 2021–25 previously-opened first basket | BASE 0.25% | BASE 0.50% | STRESS 0.25% | STRESS 0.50% |
|---|---:|---:|---:|---:|
| Original five-year cumulative return | +34.5961% | +20.0803% | +33.6847% | +16.9500% |
| Return after *minute OPEN below STOP* extra-gap stress | +34.5961% | +20.0803% | +33.6847% | +16.9500% |
| Previous official raw hourly-close marked MTM DD | -8.6650% | -15.9596% | -8.8029% | -16.2822% |

## Hard limitations
1. Reconstructing source 1m candle STOP touching is weaker than actual order executable bid/ask/depth at first touch. A 1m OPEN may be above the stop but an intra-minute price jump can still render an actual market order far worse than the exact pre-trigger stop price.
2. The 1m gate checked original stop EXIT bars, **not a full 1m marked portfolio trace over all 43,824 hours**, and not actual exchange order creation or exchange acknowledgment.
3. Original 2021–25 rule assumed next 1h OPEN market long fill and stop at original fixed 1h bar STOP or gap OPEN, plus imposed 2/5bps per-side slippage. It did not reconstruct specific MEXC order book or MEXC 2021–25 historical funding.
4. Historical quote route feasibility **UNVERIFIED**; Binance OHLCV source does not bind historical MEXC derivatives BBO, funding, capacity, product/venue jurisdiction. MEXC official API Futures taker current as of June 2026 is 8bps PER SIDE; pair-specific applicability/regulatory conditions require verification. Fee alone is not a transfer proof.
5. Original historical first ETH/SOL/BNB local PASS is scope limited and previously seen; independent XRP/DOGE/ADA/LINK/AVAX expansion 0/5 positive and ALL13 earlier low-risk combined BASE -4.1129% remain FAIL. 2026 protected holdout remains locked, unchanged.
6. Gross funded real capital expected return and worst intra-minute drawdown are **NOT PROVEN** by 1m stop source PASS. No live trading authorization created.

## Combined scientific status, no prospective-event wait required for THIS historic classification
**RAW_SOURCE_REPRO_PASS / HOURLY_MTM_REPRO_PASS / 1MIN_STOP_PATH_SOURCE_PASS / HISTORICAL_LOCAL_SCOPE_LIMITED_PASS / HISTORICAL_13_ASSET_GENERALIZATION_FAIL / EXECUTION_FEASIBILITY_UNVERIFIED / LIVE_GO_NO**.

## Evidence
- [Canonical actual OHLCV and original funding replay](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37916963862), 1h raw source same immutable original body and full trade/funding check, artifact 11611165132.
- [Canonical full exit-hour 1m stop source audit](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37917719450), artifact 11610061502.
- [Original archived 2021–25 canonical trades](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35918769969).
- [Previous 13 asset shared risk economic audit](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37896908699).

No trades, purchases, private API, accounts/wallets or merge. Preserve exact original science.
