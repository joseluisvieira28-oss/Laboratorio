# BACKES-DIAMANTE-004 — Independent economic verdict (2026-11-24)
**Decision: ECONOMIC NO-GO.** GO only to continue a separate prospective NO-TRADING shadow sample.

## Audit authority
- Primary PR #389: https://github.com/joseluisvieira28-oss/Laboratorio/pull/389
- Source-backed GitHub Actions SUCCESS: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45337852543
- Verified artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45337852543/artifacts/14895470089
- Artifact SHA256: 73a3e5349930d8b8d8dab46fa69fb8989a118c79cb7f6f7a59260b2f50641d7b
- Original BACKES-002 Binance artifact SHA256: 735fff332994ce546f56258a01787d7f250203efa701586fa24eefd553f1ecaf
- 7/7 deterministic tests PASS, including direct BACKES002 parity and no-lookahead. Initial failed CI discovered a real future-indexing bug in the new MOM baseline, fixed **before** source-backed economic results.
- Binance: official Spot BTCUSDT ETHUSDT ETHBTC, 384 original public ZIPs, 464 weeks 2018-01-01..2026-11-22 UTC, daily->Monday-Sunday.
- Coinbase: official Exchange BTC-USD ETH-USD ETH-BTC, **51 HTTP GET responses** with source hashes, 464 weeks 2018-01-01..2026-11-22 UTC, daily->Monday-Sunday.
- Kraken initial weekly source: **SOURCE_BLOCKED**, because its official 10080-minute weekly candles are Thursday-anchored (example 2017-12-28). The full-period 2018–2026 Kraken result is therefore NOT calculated. Never re-label these weekly bars as Monday to fabricate price comparability.
- Source receipts, normalized weekly OHLC, economic CSV/JSON and full diagnostics in the linked artifact.
- All prices and model results are **RETROSPECTIVE**. A separate 004B Kraken DAILY 2025–2026 price replication is documented in PR #391 and does not retroactively remove this weekly-data source block.

## Comparison all 464 weeks; 10bps per traded portfolio fraction (hypothetical)
| Model | Coinbase cumulative net | Binance cumulative net | Coinbase MDD | Binance MDD |
|---|---:|---:|---:|---:|
| BTC hold | +340.75% | +346.28% | -80.25% | -80.09% |
| FROZEN002 original Crypto Lab swing+momentum | +546.11% | +551.33% | -82.65% | -82.50% |
| MOM4 simple relative trend | +384.24% | +390.83% | -84.49% | -84.31% |
| MOM8 simple relative trend | +552.25% | +557.34% | -82.69% | -82.67% |
| MOM12 simple relative trend | +98.76% | +91.74% | -85.47% | -85.45% |

**No stable advantage of complex vs simple model:** MOM8 marginally exceeds FROZEN002 over all years; both have unacceptably severe historic drawdowns. This is not a statistically independent discovery.

## Separated economic regimes (10bps)
| Model | Coinbase 2018–22 | Coinbase 2023–24 | Coinbase 2025–26 |
|---|---:|---:|---:|
| BTC | +19.71% | +491.43% | -37.87% |
| MIX weekly 50/50 | +71.45% | +336.52% | -43.83% |
| FROZEN002 | +61.04% | +317.81% | -4.17% |
| MOM4 | +124.06% | +159.35% | -16.84% |
| MOM8 | +130.75% | +277.47% | -25.19% |
| MOM12 | -23.67% | +208.09% | -15.65% |

Binance follows almost the same rank and economic regimes, as documented in ECONOMIC.json. FROZEN002 fails against plain BTC in 2023–24 and a 50/50 portfolio in 2018–22, as already seen in predecessor evidence. Its 2025–26 loss reduction is concentrated in one earlier-seen ETH regime; only two switches, not enough independent events.

## Realistic current first-tier taker fee stress, NOT actual 2018–26 account fees
2026-11-24 official Coinbase Exchange fee table https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees: small-tier 60bps taker, 40bps maker.
2026-11-24 Kraken Pro Spot fees https://www.kraken.com/pro/fees: first-tier 80bps taker, 40bps maker.
These published first-tier fees EXCLUDE spread/slippage and differ by account, venue, calendar year, volume tier, order type and product. The experiments do not reconstruct dated actual fills or real historic fee tier schedules.
- At Coinbase 60bps/leg over 2018–26: FROZEN002 +385.40%, MOM8 +352.21%, BTC +338.54%. Despite positive cumulative difference, the 82%+ MDD and strong regime concentration invalidate a trading GO.
- At 80bps/leg over 2018–26: Coinbase FROZEN002 +332.75% vs BTC +337.66%; Binance FROZEN002 +342.43% vs BTC +343.15%. **The original complex model fails to beat BTC with this stress.**
- At 100bps/leg: Coinbase FROZEN002 +285.73% vs BTC +336.78%; Binance FROZEN002 +295.95% vs BTC +342.26%.
- The Binance 80bps scenario is cross-venue sensitivity, NOT the confirmed Binance account fee.

## Rolling chronological selector; 104-week training / 26-week next folds
- 14 consecutive chronological test folds from late 2019 through 2026-11-22; candidate pool FROZEN002/MOM4/MOM8/MOM12, choose net 104w return before each 26w segment, no test-window tuning.
- Coinbase selected compounded +1481.10%, BTC +727.43%, 50/50 +1127.45%, selected MDD **-71.68%**.
- Binance selected compounded +1481.64%, BTC +728.45%, 50/50 +1129.07%, selected MDD **-71.66%**.
- Fold selection frequencies the same across Coinbase/Binance: MOM8 6, MOM4 4, FROZEN002 4, MOM12 0.
- **PSEUDO-OOS ONLY:** research team saw and used the 2018–2026 performance before defining this comparison in November 2026. The algorithm's chronological splits do not make past history independent of hypothesis selection.

## Statistical limitation
Eight-week moving-block bootstrap on the 2025–26 weekly return excess:
- Coinbase FROZEN002 vs BTC mean +0.50396 percentage points weekly, CI95 [-0.08602, +1.58581]; includes zero.
- Binance FROZEN002 vs BTC mean +0.50397 pp weekly, CI95 [-0.08613, +1.58601]; includes zero.
- All other FROZEN/MOM4/MOM8/MOM12 weekly excess CI95 vs BTC and MIX include zero in this period.
- Descriptive intervals lack correction for post-hoc model search and cannot be claimed as prospective significance.

## Verdict
**NO-GO for economic edge, orders, capital or automated live trading.**
**SOURCE_PASS** for independent Coinbase and Binance 2018–26 market histories; **SOURCE_BLOCKED** for Kraken 1w Monday anchor, with recent 1d price check separate in BACKES004B.
**CANDIDATE ONLY** for separately frozen prospective shadow observation; requires independent future observations with prices after timestamped decisions, full account-specific fees, adverse liquidity, multiple regimes and a drawdown acceptance criterion before considering any economic GO.

Zero trades, account access, API keys, subscriptions, payments, deployments, merges or transfers. No assertion about Augusto Backes personal financial results; these are Crypto Lab original hypotheses.
