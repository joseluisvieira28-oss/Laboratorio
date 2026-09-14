# STABLECOIN-EXCHANGE-FLOW-001 — PRE-SOURCE PROTOCOL V0.1

STATUS: FROZEN PRE-OUTCOME / SOURCE-PROVENANCE GATE NEXT

LAB: `STABLECOIN-EXCHANGE-FLOW-001`
MVE: `SEF-USDT-EXFLOW-1D-001`

## Scientific question

Does aggregate USDT net flow into centralized exchanges predict a positive subsequent BTC return when the flow signal is known without lookahead?

This is materially distinct from `ONCHAIN-CAPFLOW-001`, which tested USDT+USDC circulating-supply growth rather than exchange inflow/outflow.

## Frozen economic mechanism

USDT moving from non-exchange wallets into exchange-controlled wallets creates immediately deployable crypto buying power. The primary direction is therefore:

- positive USDT net inflow to exchanges -> expected positive subsequent BTC return;
- negative USDT net inflow -> expected negative subsequent BTC return.

No BTC/ETH on-chain flow, funding, OI, ETF, price, sentiment, volume or technical filter is part of MVE0.

## Preferred source family

Primary candidate: Coin Metrics Network Data Pro aggregate exchange-flow metrics for asset `usdt`:

- `FlowInExNtv` — aggregate deposits to exchanges, excluding exchange-to-exchange transfers where defined by provider methodology;
- `FlowOutExNtv` — aggregate withdrawals from exchanges;
- `net_flow_t = FlowInExNtv_t - FlowOutExNtv_t`.

Frequency candidate: 1 day.

Protected source window for a future Discovery, if and only if provenance passes: 2021-01-01 through 2024-12-31.

2025 and 2026 remain forbidden during source gate and Discovery.

## Critical point-in-time provenance rule

This family MUST NOT treat a current reconstructed exchange-address history as automatically tradable historical information.

Coin Metrics documents that exchange-flow metrics are based on exchange-address identification/clustering and has publicly announced historical recalculations after newly discovered exchange addresses. Therefore the source gate must separately establish whether the historical values can be defended as point-in-time observable or whether the provider can expose adequate historical constituent/timeframe/version evidence.

If point-in-time observability cannot be defended, classification is `SOURCE_PIT_BLOCKED`, even if the API returns complete numeric history.

No override is allowed because the series "looks good" later.

## Frozen source-gate sequence

1. Probe official Coin Metrics Community/API routes without credentials for the exact metric family and protected historical window.
2. Record HTTP status, response schema and whether historical rows are accessible.
3. Probe official reference/catalog metadata for metric availability and any constituent/timeframe metadata useful for point-in-time provenance.
4. Do not access BTC prices, compute returns, strategy PnL or predictive statistics.
5. Do not access any 2025/2026 flow rows.

## Future MVE signal — frozen concept, not yet executable

Only if the source/provenance gate passes:

`net_flow_t = FlowInExNtv_t - FlowOutExNtv_t`

No rolling threshold, z-score, percentile, ML model or feature combination is authorized in MVE0.

Because the daily network metric summarizes activity during day t, a future Discovery must use a conservative information-safe timestamp no earlier than the completion of that daily interval plus an explicit provider-publication buffer frozen before outcome access.

Primary test direction: beta > 0 in a single pre-registered regression of subsequent BTC return on USDT net flow. Companion sign strategy may be defined only before Discovery and may not be tuned after outcomes.

## Hard governance

- research-only;
- fail-closed;
- no live trading;
- no exchange mutation;
- no merge to main;
- no deployment;
- no post-outcome tuning;
- no 2025/2026 access;
- no fallback to total stablecoin supply (already tested separately);
- no fallback to DEX peg/liquidity (different lab);
- no paid-data purchase without separate authorization.

## Source-gate classifications

- `SOURCE_PROVENANCE_PASS`
- `SOURCE_AUTH_BLOCKED`
- `SOURCE_PIT_BLOCKED`
- `DATA_FAILURE`
- `TECHNICAL_FAILURE_PREOUTCOME`

Only `SOURCE_PROVENANCE_PASS` can authorize creation of a final pre-Discovery protocol.
