# CRYPTO-ILLIQUIDITY-PREMIUM-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35499690675`
MVE: `CIP-MAJOR5-WEEKLY-AMIHUD-001`

## Source

**CIP_SOURCE_FULL**

BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT and XRPUSDT each had complete monthly Binance USD-M daily-kline coverage across 2021-2025.

## Verdict

**DISCOVERY_FAIL_NO_PROMOTION**

Only the frozen 2021-2023 Discovery was opened. The conditional 2024-2025 holdout remained closed.

Primary 20 bps result:
- N = 154 weekly portfolios
- mean net = +1.6002%
- median = -0.2396%
- hit rate = 49.35%
- PF = 1.6012
- bootstrap 95% CI mean = [-0.2295%, +3.6845%]
- positive years = 2 / 3
- 2021 = +4.5278%
- 2022 = -0.0164%
- 2023 = +0.2270%

Stress 40 bps:
- mean net = +1.4002%
- PF = 1.5064
- 2021 = +4.3278%
- 2022 = -0.2164%
- 2023 = +0.0270%

All frozen gates passed except the bootstrap 95% lower bound > 0.

The point estimates are economically positive and survive the frozen 40 bps stress, but uncertainty remains too large under the prospectively frozen standard. The 2024-2025 holdout is therefore not opened.

No post-outcome change to the 20-day Amihud window, weekly rebalance, universe, top2/bottom2 construction, costs or horizon is authorized. No 2026 data, live trading, exchange mutation, wallet access or merge to main occurred.
