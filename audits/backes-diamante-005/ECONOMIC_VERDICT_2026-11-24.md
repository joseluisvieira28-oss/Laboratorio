# BACKES-DIAMANTE-005 — Independent risk/economic verdict, 2026-11-24

**TECH PASS / ECONOMIC NO-GO / NO REAL TRADES.** Research-only, all historical dates 2018–2026 retrospectively known to research team. These are Crypto Lab hypotheses, NOT Augusto Backes' proprietary trading record.

## Verifiable evidence
- Draft PR: https://github.com/joseluisvieira28-oss/Laboratorio/pull/392
- GitHub Actions job SUCCESS (7/7 offline tests, full economic job success): https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45363955755
- Original full results ZIP: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45363955755/artifacts/14905194443
- BACKES-005 ZIP SHA256: c3ea39d6d4b0062ba25364faee6bb4be6ba5cb4f1bf41a6404a158bd3e5a21ea
- Source immutable BACKES-004 ZIP SHA256: 73a3e5349930d8b8d8dab46fa69fb8989a118c79cb7f6f7a59260b2f50641d7b
- BACKES-004 WEEKLY_DATA.json SHA256: 4e256e2f0d4359943f96e9b1eb87e7cfe8cd6d6ca07728db7d5aa2dd4800d828
- BACKES-004 ECONOMIC.json SHA256: aa7305b470b3e4623965216608ef80c932682ac072b254c75b1200771454beb2
- Coinbase Exchange BTC-USD / ETH-USD / ETH-BTC, Binance Spot BTCUSDT / ETHUSDT / ETHBTC, 464 Monday–Sunday weeks UTC, Jan 1 2018 through Nov 22 2026. Original BTC, ETH, MOM8 and FROZEN002 performance reproduced to 0.00015pp.
- Pre-source frozen protocol at commit bea8d6125f540194887c002328284d22e865a551. Six risk overlays, parameters 40-week trend / 12-week vol / annual volatility target 20% fixed before results.
- 10/35/60/80/100 bps all-in hypothetical per traded notional, 80bps two-hop; no historical orderbook fill, historical account fee tier, stablecoin depeg/custody or terminal liquidation costs established.

## Whole period 2018–2026 — 80bps all-in spot friction
| Model | Coinbase annual CAGR | Coinbase weekly MDD | Binance annual CAGR | Binance weekly MDD |
|---|---:|---:|---:|---:|
| FROZEN002 (100% allocated rotation) | +17.91% | -82.89% | +18.20% | -82.75% |
| HALF_ROT (50% cash) | +14.24% | -54.43% | +14.14% | -54.19% |
| BTC_TREND40 | +32.11% | -50.46% | +32.27% | -50.43% |
| ROT_TREND40 | +38.19% | -56.44% | +38.37% | -56.32% |
| MOM8_TREND40 | +43.45% | -49.88% | +43.67% | -49.89% |
| ROT_TREND40_VOL20 | +15.04% | -23.21% | +15.31% | -23.38% |
| MOM8_TREND40_VOL20 | +14.82% | -22.55% | +15.08% | -22.53% |

The apparent risk reduction partly reflects significant cash exposure: ROT_TREND40_VOL20 only 22.64% Coinbase / 22.72% Binance average invested; MOM8 version 20.79% / 20.87%; both 192 of 464 weeks wholly in cash.

Weekly low/OHLC proxy drawdowns are -24.28% Coinbase / -24.37% Binance ROT_VOL20, and -23.76% / -23.74% MOM8_VOL20. These low-bar proxies do NOT measure genuine intraday traded PnL, stops or guaranteed capital floors.

## Regime breakdown — Binance, 80bps
| Period | ROT_TREND40_VOL20 net return / MDD | MOM8_TREND40_VOL20 net return / MDD |
|---|---:|---:|
| 2018–2022 | +114.92% / -23.38% | +167.74% / -15.40% |
| 2023–2024 | +71.72% / -17.69% | +52.12% / -11.20% |
| 2025–2026 | -4.15% / -20.45% | -14.41% / -22.53% |

2025–2026 benchmark CASH +0% in model and HALF_ROT +1.35% / -29.91% DD, against FROZEN002 -6.01% / -52.31% DD. This shows exposure reduction, NOT consistent prediction.

## Statistical limits and GO gate
The 2025–2026 Binance ROT_VOL20 weekly excess vs CASH: -0.0185 percentage points, 8-week moving-block bootstrap 95% CI [-0.4325,+0.5637] percentage points (includes zero). Other comparator confidence intervals also include zero; not adjusted for multiple tests or post hoc hypothesis selection.

**0 of 6 research candidates.** The two VOL20 strategies pass full-period pre-frozen MDD <=30%, >20pp improvement vs FROZEN002 and full-period risk-adjusted criteria in both exchanges, but only pass 1 of 3 major regime comparisons, not the 2/3 required. Their 2025–26 results are negative. Neither 80bps friction nor 10bps models imply execution-quality fills. LIVE ECONOMIC NO-GO.

## Red-team accounting issue found, did not tune any strategy
Prior BACKES-004 50/50 benchmark undercharged the initial buy by half: 50% BTC purchase + 50% ETH purchase is 100% of NAV traded, not 50% (old max(abs(deltaBTC),abs(deltaETH)) rule). BACKES-005 corrects this with max(total buys, total sells) for one-leg netted spot and records exact difference in research/backes-diamante-005/ACCOUNTING_FINDING_004.md.

At 10bps: Coinbase old +320.85333% should be corrected to ~+320.64280%; Binance old +326.33208% to ~+326.11881%. FROZEN002/MOM8/BTC/ETH parity unchanged. Original BACKES-004 report is kept immutable; do not misrepresent this as newfound trading edge.

## Decision and boundaries
**SOURCE PASS / 7/7 TECH PASS / LIVE ECONOMIC NO-GO.** The volatility targets are two retrospective ideas worth separate pre-frozen prospective, read-only comparison, not deployment. No changes to thresholds after this outcome, no new optimized variants on the same sample, no trades/orders, subscriptions/payments, account access or production merge.
