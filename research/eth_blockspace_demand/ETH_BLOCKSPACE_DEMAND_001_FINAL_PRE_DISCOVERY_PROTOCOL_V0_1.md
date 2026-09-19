# ETH-BLOCKSPACE-DEMAND-001 — FINAL PRE-DISCOVERY PROTOCOL V0.1

Date: 2026-09-19
Branch: `eth-blockspace-demand-v0.1`
Status: **FROZEN PRE-MARKET-OUTCOME**

Canonical source-data authority:
- Source recovery run: **35446488521**
- Artifact: **10585049563**
- Artifact digest: **sha256:6bd5b8970a07fa022d91710b956a0ed80468fee3417c16d02746be6eb1e71114**
- Daily source series SHA-256: **1fffaf5dde2a1cff10356333536a6660a22f35e56210f376081738ea394bc928**
- Sampled blocks SHA-256: **f1324568b8002948b6b13e2a687d8fb8a7d9fe9bbb20e9704b0804efa8d90e8a**
- Source coverage: 4,723 / 4,723; 237 / 237 cross-provider audits; daily retention 99.84%.
- No market prices, returns or PnL were opened before this freeze.

## 1. Candidate ID

`EBD-BURN80-UTIL50-LONG-H24-001`

Primary Edge Family: **SUPPLY / FLOW**
Secondary context: **protocol blockspace demand**

## 2. Mechanism statement

A day with unusually high Ethereum protocol base-fee burn combined with above-normal block gas utilization represents unusually strong blockspace demand while ETH is simultaneously removed from supply through EIP-1559 base-fee burn.

If that protocol demand/supply pressure is not fully capitalized contemporaneously, ETH should have positive next-day directional expectancy after realistic trading costs.

## 3. Failure mode

The hypothesis should fail if:
- blockspace spikes are purely contemporaneous with price moves and contain no lead information;
- high fees reflect panic/liquidations or temporary congestion rather than persistent demand;
- activity migrates away while fees spike;
- the market prices protocol demand immediately.

No regime, asset, direction or threshold rescue is permitted after outcomes.

## 4. Source signal

Canonical daily fields:
- `mean_sample_block_base_fee_burn_eth`
- `mean_gas_utilization`

For source date t, use only the **previous 90 canonical daily observations** to compute:
- prior90 burn empirical 80th percentile;
- prior90 utilization median.

Signal is TRUE on day t iff BOTH:
1. current `mean_sample_block_base_fee_burn_eth >= prior90 burn 80th percentile`;
2. current `mean_gas_utilization >= prior90 utilization median`.

No other filter.

The current day's Ethereum source series is considered known only after that UTC day has fully closed.

Source-only pre-freeze census:
- Discovery-window signal dates: **112**
- 2024 holdout-window signal dates: **43**
This census contains no market outcome information and may not be used to alter thresholds after this freeze.

## 5. Market target

Instrument: **Binance Spot ETHUSDT**
Direction: **LONG only**

Discovery market source:
- Binance Data Vision monthly Spot `1d` archives
- exactly 2022-01 through 2023-12
- provider checksum required for every archive
- no 2024, 2025 or 2026 market archive may be requested during Discovery.

## 6. Timing

Discovery source signal dates:
- 2022-01-01 through 2023-12-29 inclusive.

For signal date t:
- entry = ETHUSDT open at t+1 UTC day;
- exit = ETHUSDT open at t+2 UTC day;
- raw return = exit / entry - 1.

This is a fixed **24-hour hold**.

No stop, target, trailing exit, leverage or intraday timing.

## 7. Costs

BASE round-trip cost: **20 bps**
STRESS round-trip cost: **30 bps**

Net bps = raw return bps - frozen round-trip cost.

Costs may not be reduced after outcomes.

## 8. Independence / overlap

Every eligible source signal is a primary event.
Because holding period is exactly 24h, consecutive daily signals may produce adjacent non-overlapping positions.
No same-day duplicate position exists.

## 9. Discovery statistics

Primary sample only:
- n
- mean and median BASE net bps
- BASE profit factor
- positive fraction
- STRESS mean and profit factor
- cumulative additive BASE bps
- max additive drawdown bps
- largest single positive-event share of total positive BASE PnL
- 2022 and 2023 separate metrics
- UTC calendar-week block bootstrap, 10,000 repetitions, seed 20260919, 95% CI
- one-sided bootstrap p for mean > 0.

There is one primary hypothesis only. No parameter family or FDR search is authorized.

## 10. Discovery PASS

`DISCOVERY_SURVIVES` requires ALL:
1. resolved n >= 100;
2. BASE mean net bps > 0;
3. BASE PF > 1;
4. STRESS mean net bps > 0;
5. bootstrap lower 95% > 0;
6. one-sided bootstrap p <= 0.05;
7. 2022 BASE mean > 0;
8. 2023 BASE mean > 0;
9. largest single positive event share <= 20%.

Otherwise the exact candidate closes as:
- `DISCOVERY_NO_EDGE` if n>=100 but gates fail;
- `INSUFFICIENT_SAMPLE` if n<100.

## 11. Locked 2024 OOS

2024 ETHUSDT market outcomes remain CLOSED during Discovery.

Only `DISCOVERY_SURVIVES` authorizes a separate frozen 2024 OOS protocol.

The OOS source signal dates are already mechanically determined by the pre-market source series, but their market outcomes must not be opened in this Discovery run.

## 12. Governance

Research-only.
No 2024/2025/2026 market data in Discovery.
No live trading.
No exchange mutation.
No orders.
No wallets.
No alerts/webhooks.
No Render deployment.
No merge to main.
No post-outcome threshold, direction, horizon, asset, cost or regime tuning.
