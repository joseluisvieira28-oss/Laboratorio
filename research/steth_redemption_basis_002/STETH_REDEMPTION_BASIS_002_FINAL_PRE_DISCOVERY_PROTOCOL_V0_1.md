# STETH-REDEMPTION-BASIS-002 — FINAL PRE-DISCOVERY PROTOCOL V0.1

Status: **FROZEN BEFORE ECONOMIC OUTCOMES / SOURCE_DATA_PASS VERIFIED**
Date: **2026-09-18**
Branch: `steth-redemption-basis-002-source-v0.1`

## 0. Source authority and lineage

This is a NEW experiment. It does not reopen or rescue STETH-REDEMPTION-BASIS-001.

STETH-REDEMPTION-BASIS-001 remains terminal:
`FROZEN_SOURCE_BOUNDARY_PROVENANCE_FAILURE`.

STETH-REDEMPTION-BASIS-002 has independently passed its source gate before this economic protocol was frozen.

Canonical source receipt:
- run: `35386033845`
- artifact: `10563803871`
- artifact digest: `sha256:d1c371d5dda3718bb044f9a6b2cd628d8c35cd55af8ba85040375ee903110f53`
- classification: `SOURCE_DATA_PASS`
- frozen first mapped snapshot block: `17,272,128`
- frozen final mapped snapshot block: `21,522,315`
- expected daily snapshots: `596`

Source gate opened no market prices, returns or PnL.

## 1. Hypothesis

A sufficiently large executable secondary-market discount of stETH to its protocol redemption value can create a positive ETH-denominated convergence payoff after Curve slippage/fee, queue opportunity cost, gas and a fixed protocol-risk buffer.

Economic sign:

**buy stETH with ETH -> request protocol withdrawal -> claim ETH**

No ETH price direction is predicted.
No short leg.
No leverage.

## 2. Frozen universe and clock

- chain: Ethereum mainnet only;
- secondary venue: Curve legacy ETH/stETH pool `0xDC24316b9AE028F1497c275EB9192a3Ea0f67022` only;
- redemption venue: Lido WithdrawalQueueERC721 `0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1` only;
- source period: **2023-05-16 through 2024-12-31 inclusive**;
- candidate observation: first Ethereum block at/after **12:00:00 UTC each calendar day**;
- expected observation universe: **596 daily snapshots**;
- first frozen observation: `2023-05-16T12:00:00Z`;
- last frozen observation: `2024-12-31T12:00:00Z`;
- 2025 and 2026: locked.

No alternate DEX, alternate LST, intraday best-time selection, threshold sweep or period substitution is allowed.

## 3. Frozen notional and executable quote

Initial notional per hypothetical trade:

**10.000000 ETH**

At snapshot block `t`:

- call Curve `get_dy(0,1,10 ETH)` to obtain `stETH_quote_t`;
- the quote is treated as the deterministic AMM output for the frozen notional and already embeds pool fee and pool-state slippage;
- apply an additional base quote-to-fill haircut of **2 bps** to stETH output;
- stress quote-to-fill haircut: **5 bps**.

No mark, external index, CEX price or later best execution may replace this quote.

## 4. Frozen queue / redemption mechanics

Immediately after the hypothetical Curve acquisition, the full acquired stETH amount is assumed submitted to Lido withdrawal in the next block.

The hypothetical queue position is:

`getLastRequestId(t) + 1`

For later realized holding-time reconstruction, finalization time is the first canonical `WithdrawalsFinalized` event whose finalized `to` request id is >= that hypothetical queue position.

This uses FIFO queue progression and is frozen before outcomes.

Base maximum allowed realized wait:

**14 calendar days**

A hypothetical position not finalizable within 14 days is classified operationally failed for this MVE; it is not silently extended.

Redemption value follows Lido protocol mechanics:
- nominal where finalization is 1:1 in stETH terms;
- if the corresponding finalization checkpoint is discounted because protocol share rate fell, use the lower protocol-defined claimable ETH amount.

The implementation must reproduce Lido's contract-level claim calculation from point-in-time request shares/checkpoint data.

No assumed 1:1 override is allowed if canonical protocol state implies less.

## 5. Frozen point-in-time cost model

### 5.1 Foregone stETH rewards

stETH placed in the withdrawal queue no longer receives staking rewards.

At entry, compute a trailing **7-day annualized stETH reward rate** using only canonical `TokenRebased` events available by snapshot block `t`.

For the ex-ante signal estimate:

- queue backlog = canonical `unfinalizedStETH()` at `t`;
- trailing throughput = total ETH finalized by canonical withdrawal finalizations during the preceding 14 calendar days, using only events available by `t`;
- estimated queue days = backlog / (trailing-14d-finalized-ETH / 14), with a floor of 0.25 day;
- if trailing throughput is zero or estimated queue days > 14, no signal.

Estimated foregone rewards use the acquired stETH amount, trailing 7-day reward rate and estimated queue days.

For realized Discovery PnL, opportunity cost uses the actual reconstructed holding time, not a future-known estimate at entry.

### 5.2 Gas

Base gas model:

**800,000 total gas units**

Point-in-time gas price proxy:

`1.25 × baseFeePerGas` from snapshot block `t`.

Base gas cost in ETH:

`800000 × gas_price_proxy`

Stress gas cost:

**1.5 × base gas cost**

No later lower-gas rescue is allowed.

### 5.3 Protocol-risk reserve

Base fixed protocol-risk reserve:

**10 bps of initial ETH notional**

Stress protocol-risk reserve:

**25 bps of initial ETH notional**

This reserve is a research conservatism term, not an estimate of Lido loss probability.

## 6. Frozen predictor

Define:

`acquired_steth_base_t = Curve_get_dy_10ETH_t × (1 - 0.0002)`

`expected_nominal_redemption_eth_t = acquired_steth_base_t`

unless canonical point-in-time protocol state already requires a lower redemption value.

`estimated_queue_reward_cost_eth_t = acquired_steth_base_t × trailing_7d_APR_t × estimated_queue_days_t / 365`

`gas_cost_eth_t = 800000 × 1.25 × baseFeePerGas_t`

`risk_reserve_eth = 10 ETH × 0.0010`

`estimated_net_edge_eth_t = expected_nominal_redemption_eth_t - 10 ETH - estimated_queue_reward_cost_eth_t - gas_cost_eth_t - risk_reserve_eth`

Signal if and only if:

1. every required source field is available point-in-time;
2. estimated queue days <= 14;
3. `estimated_net_edge_eth_t > 0`.

No secondary threshold.
No percentile tuning.
No regime filter.
No selection of the historically strongest days.

## 7. Frozen execution and overlap

- one hypothetical position maximum at a time;
- if a prior hypothetical withdrawal has not reached its reconstructed finalization/claim point, later daily signals are ignored;
- no stop-loss;
- no take-profit;
- no early sale back to Curve;
- exit only through Lido claim;
- no leverage.

## 8. Frozen outcome

Primary outcome:

**realized net ETH gain/loss from the 10 ETH starting notional**

after:
- frozen Curve quote-to-fill haircut;
- protocol-defined realized claim amount;
- realized queue opportunity cost from stETH rewards foregone over reconstructed wait;
- base gas model;
- base protocol-risk reserve.

Secondary diagnostics only, never rescue criteria:
- holding days;
- gross discount captured;
- gas share of gross spread;
- queue-cost share of gross spread;
- stress net ETH.

No BTC/ETH directional return is part of the primary outcome.

## 9. Frozen sample and promotion gates

All are required:

1. at least **30 completed non-overlapping hypothetical redemptions**;
2. mean base net ETH per trade > 0;
3. median base net ETH per trade > 0;
4. >= 70% of completed trades base-net positive;
5. stationary/block-bootstrap 95% lower confidence bound for mean base net ETH > 0;
6. 2023 and 2024 each have >= 10 completed trades and non-negative mean base net ETH;
7. largest single positive trade contributes <= 30% of total positive base contribution;
8. stress mean net ETH > 0 using 5 bps fill haircut, 1.5x gas and 25 bps protocol-risk reserve;
9. zero provenance/leakage violations.

Failure of any promotion gate means no promotion under V0.1.

No sign, notional, snapshot time, venue, queue horizon, cost or period rescue after outcomes.

## 10. Classification

If fewer than 30 completed non-overlapping hypothetical redemptions are generated:

`DISCOVERY_INSUFFICIENT_SAMPLE`

If sample gate passes but any promotion gate fails:

`DISCOVERY_NO_REDEMPTION_EDGE`

If all frozen gates pass:

`DISCOVERY_REDEMPTION_EDGE_PASS_REQUIRES_SEPARATE_REPLICATION`

A Discovery pass is not Tier 2/Tier 1, not production and not live-trading authority.

## 11. Discovery authorization and firewall

Because STETH-REDEMPTION-BASIS-002 has an exact `SOURCE_DATA_PASS`, this frozen protocol authorizes one exact Discovery execution using only the rules above.

Forbidden:
- 2025 or 2026 data;
- alternate venues or LSTs;
- alternate snapshot clock;
- alternate notional;
- threshold, horizon or cost rescue;
- market-direction return testing;
- live trading;
- wallet access;
- exchange mutation;
- main merge.

The exact source receipt and this exact protocol must be bound into the Discovery receipt.
