# MEXC AMD FEE-AWARE LARGE-LAG — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE AMD OUTCOMES

## Why this hypothesis exists

The replicated low-threshold stock-futures signal (5 bps external shock / 3 bps lag gap / 1m FOLLOW) survives across multiple assets but typically produces only ~3–4 bps gross, below known standard MEXC API round-trip fees.

AMD V0.2 is an economically distinct test designed from the known fee barrier, not from AMD outcomes.

## Sources

Target:
- MEXC `AMDSTOCK_USDT`

External:
- Binance `AMDUSDT`
- Bitget `AMDUSDT`

Source census:
- run `37230403276`
- verdict `FEEAWARE_EQUITY_SOURCE_PASS__AMD`
- source day `2026-09-30`, excluded from outcomes

## Frozen sample

- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30
- signal window 14:31–18:44 UTC
- exact 1m observable alignment
- no forward fill/interpolation

## Exact fee-aware signal

External return:
`mean(Binance AMDUSDT 1m return, Bitget AMDUSDT 1m return)`

Lag gap:
`external return - MEXC AMDSTOCK_USDT 1m return`

Signal requires:
- abs(external return) >= 20 bps
- sign(lag gap) == sign(external return)
- abs(lag gap) >= 10 bps

Direction:
`FOLLOW_EXTERNAL_CONSENSUS`

Horizon:
`1 minute`

Cooldown:
`1 minute`

No grid search.

## Scientific PASS

Requires all:
- N>=20
- >=8 distinct signal sessions
- mean gross >0
- median gross >0
- win rate >50%
- all three chronological thirds mean >0
- exact one-sided binomial p<0.05

## Execution-scale PASS

Separately requires:
- mean gross >16 bps
- median gross >12 bps

The 16 bps mean threshold is frozen from the known upper standard API fee-only round-trip case (taker/taker), before spread/slippage.

Possible classifications:
- `FEEAWARE_SCIENTIFIC_AND_EXECUTION_SCALE_PASS__FORWARD_VALIDATION_REQUIRED`
- `FEEAWARE_SCIENTIFIC_SIGNAL__EXECUTION_SCALE_FAIL`
- `FEEAWARE_AMD_UNDERPOWERED`
- `NO_EDGE_FEEAWARE_AMD`

No tuning, private endpoints, account reads, wallets, orders, exchange mutation or live trading.
