# STABLECOIN-SUPPLY-LIQUIDITY-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35476922006`
Workflow head: `1dd483a0f6cb008a470840ef420fcccb427e07db`
MVE: `SSLI-USDTUSDC-7D-IMPULSE-001`

## Source gate

**SSLI_SOURCE_FULL**

Both bounded Coin Metrics Community supply series passed:
- USDT: 1,675 daily observations, 2020-06-01 through 2024-12-31
- USDC: 1,675 daily observations, 2020-06-01 through 2024-12-31
- 100% non-null and positive supply observations
- no credentials, zero cash cost
- no 2025/2026 request

## Discovery verdict

**INSUFFICIENT_SAMPLE**

Only 2021-2023 market outcomes were opened. 2024 replication remained locked.

Frozen 7-day positive supply-impulse event study:
- N = 21 non-overlapping events
- mean future BTC/ETH equal-weight 7d log return = +2.0056%
- median = -0.2482%
- hit rate = 42.86%
- bootstrap 95% CI mean = [-1.9763%, +6.9752%]
- positive years = 2 / 3
- 2021 mean = +4.7517%
- 2022 mean = -2.2969%
- 2023 mean = +1.9486%
- mean prior 7d market return = +1.3354%

Frozen gates passed:
- mean > 0
- >=2 positive years

Frozen gates failed:
- N >= 30
- bootstrap lower > 0
- hit rate > 50%

Because multiple economic gates fail in addition to sample size, the 2024 replication is not opened. The exact MVE is not rescued by lowering the event threshold or changing the horizon after outcomes.

No PnL, execution claim, 2024 replication, 2025/2026 data, live trading, wallet access, exchange mutation or merge to main occurred.
