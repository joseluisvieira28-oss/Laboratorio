# SP500 PUBLIC BBO EXECUTION DIAGNOSTIC V0.3

Date: 2026-10-04
Status: OFF-HOURS DIAGNOSTIC ONLY / PUBLIC MARKET DATA / NO TRADING

## Scientific input

The frozen SP500 basis signal replicated in August and September:

- symbol: `SPX500_USDT`
- signal: FADE contract/index basis
- threshold: 5 bps
- horizon: 15 minutes
- September mean gross: +0.5177567737 bps per accepted signal

## Question

Can public top-of-book spread alone already consume the observed gross edge?

This probe measures current public MEXC order-book BBO only.

## Important session caveat

2026-10-04 is Sunday.

MEXC Global Asset markets can have materially different liquidity outside primary underlying-market hours.

Therefore this run is explicitly:

`SUNDAY_OFF_HOURS_DIAGNOSTIC_ONLY`

It may identify an obviously hostile spread regime, but it may NOT be used to kill or promote the weekday execution route.

## Frozen probe

- symbol: `SPX500_USDT`
- endpoint: public `GET /api/v1/contract/depth/SPX500_USDT`
- snapshots: 60
- interval: 1 second
- depth limit: 5
- no authentication
- preserve raw summary statistics only; no orders

For each valid snapshot:

`mid = (best_ask + best_bid) / 2`

`spread_bps = 10000 * (best_ask - best_bid) / mid`

Report:
- valid/invalid snapshots
- p10 / p25 / p50 / p75 / p90 / max spread bps
- mean spread bps
- best bid/ask size medians
- fraction of snapshots with spread below the September gross edge (0.5177567737 bps)

## Interpretation

This is not a profitability gate.

If Sunday p50 spread exceeds the signal gross edge, classify:
`OFF_HOURS_SPREAD_HOSTILE`.

If Sunday p50 is below it:
`OFF_HOURS_SPREAD_NOT_OBVIOUSLY_FATAL`.

Neither result authorizes live trading or substitutes for signal-time weekday shadow fills, slippage, fees, or market impact.
