# STETH-REDEMPTION-BASIS-001 — FINAL PRE-DISCOVERY PROTOCOL V0.1

Status: **FROZEN BEFORE OUTCOMES / DORMANT UNTIL SOURCE_DATA_PASS**  
Date: **2026-09-17**

This document freezes the later Discovery design. It does not authorize Discovery by itself.

## 1. Hypothesis

A sufficiently large executable secondary-market discount of stETH to its protocol redemption value can create a positive ETH-denominated convergence payoff after Curve slippage/fee, queue opportunity cost, gas and a fixed protocol-risk buffer.

Economic sign: **buy stETH with ETH -> request protocol withdrawal -> claim ETH**.

No ETH price direction is predicted. No short leg. No leverage.

## 2. Frozen universe and clock

- chain: Ethereum mainnet only;
- secondary venue: Curve legacy ETH/stETH pool `0xDC24316b9AE028F1497c275EB9192a3Ea0f67022` only;
- redemption venue: Lido WithdrawalQueueERC721 `0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1` only;
- source period: 2023-05-15 through 2024-12-31 inclusive;
- candidate observation: first Ethereum block at/after **12:00:00 UTC each calendar day**;
- expected observation universe: 597 daily snapshots;
- 2025 and 2026: locked.

No alternate DEX, alternate LST, intraday best-time selection, threshold sweep or period substitution is allowed under V0.1.

## 3. Frozen notional and executable quote

Initial notional per hypothetical trade: **10.000000 ETH**.

At snapshot block `t`:
- call Curve `get_dy(0,1,10 ETH)` to obtain `stETH_quote_t`;
- the quote is treated as the deterministic AMM output for the frozen notional and already embeds pool fee and pool-state slippage;
- apply an additional base quote-to-fill haircut of **2 bps** to stETH output;
- stress quote-to-fill haircut: **5 bps**.

No mark, external index, CEX price or later best execution may replace this quote.

## 4. Frozen queue / redemption mechanics

Immediately after the hypothetical Curve acquisition, the full acquired stETH amount is assumed submitted to Lido withdrawal in the next block.

The hypothetical queue position is `getLastRequestId(t) + 1`.

For later realized holding-time reconstruction, finalization time is the first canonical `WithdrawalsFinalized` event whose finalized `to` request id is >= that hypothetical queue position. This uses FIFO queue progression and is frozen before outcomes.

Base maximum allowed realized wait: **14 calendar days**. A hypothetical position not finalizable within 14 days is classified operationally failed for this MVE; it is not silently extended.

Redemption value follows Lido protocol mechanics:
- nominal where finalization is 1:1 in stETH terms;
- if the corresponding finalization checkpoint is discounted because protocol share rate fell, use the lower protocol-defined claimable ETH amount.

The implementation must reproduce Lido's contract-level claim calculation from point-in-time request shares/checkpoint data. No assumed 1:1 override is allowed if the canonical checkpoint implies less.

## 5. Frozen point-in-time cost model

### 5.1 Foregone stETH rewards

stETH placed in the withdrawal queue no longer receives staking rewards.

At entry, compute a trailing **7-day annualized stETH reward rate** using only canonical `TokenRebased` events available by snapshot block `t`.

For the ex-ante signal estimate:
- queue backlog = canonical `unfinalizedStETH()` at `t`;
- trailing throughput = total ETH finalized by canonical withdrawal finalizations during the preceding 14 calendar days, using only events available by `t`;
- estimated queue days = backlog / (trailing-14d-finalized-ETH / 14), with a floor of 0.25 day;
- if trailing throughput is zero or estimated queue days > 14, no signal.

Estimated foregone rewards are calculated from the acquired stETH amount, trailing 7-day reward rate and estimated queue days.

For realized Discovery PnL, opportunity cost uses the actual reconstructed holding time, not a future-known estimate at entry.

### 5.2 Gas

Base gas model is frozen at **800,000 total gas units** across secondary acquisition + withdrawal request + claim.

Point-in-time gas price proxy: `1.25 × baseFeePerGas` from snapshot block `t`.

Base gas cost in ETH = `800,000 × gas_price_proxy`.

Stress gas cost = **1.5 × base gas cost**.

No later lower-gas rescue is allowed.

### 5.3 Protocol-risk reserve

Base fixed protocol-risk reserve: **10 bps of initial ETH notional**.

Stress protocol-risk reserve: **25 bps of initial ETH notional**.

This reserve is a research conservatism term, not a claim about expected Lido loss probability.

## 6. Frozen predictor

Define at snapshot `t`:

`acquired_steth_base_t = Curve_get_dy_10ETH_t × (1 - 0.0002)`

`expected_nominal_redemption_eth_t = acquired_steth_base_t` unless canonical point-in-time protocol state already requires a lower redemption value.

`estimated_queue_reward_cost_eth_t = acquired_steth_base_t × trailing_7d_APR_t × estimated_queue_days_t / 365`

`gas_cost_eth_t = 800000 × 1.25 × baseFeePerGas_t`

`risk_reserve_eth = 10 ETH × 0.0010`

`estimated_net_edge_eth_t = expected_nominal_redemption_eth_t - 10 ETH - estimated_queue_reward_cost_eth_t - gas_cost_eth_t - risk_reserve_eth`

Signal if and only if:
1. all source fields are available point-in-time;
2. estimated queue days <= 14;
3. `estimated_net_edge_eth_t > 0`.

No secondary threshold. No percentile tuning. No regime filter.

## 7. Frozen execution and overlap

- one position maximum at a time;
- if a prior hypothetical withdrawal has not reached its reconstructed finalization/claim point, later daily signals are ignored;
- no stop-loss;
- no take-profit;
- no early sale back to Curve;
- exit only through Lido claim;
- no leverage.

## 8. Frozen outcome

Primary outcome: **realized net ETH gain/loss** from the 10 ETH starting notional after:
- frozen Curve quote-to-fill haircut;
- protocol-defined realized claim amount;
- realized queue opportunity cost from stETH rewards foregone over the reconstructed wait;
- base gas model;
- base protocol-risk reserve.

Secondary diagnostics, never rescue criteria:
- holding days;
- gross discount captured;
- gas share of gross spread;
- queue-cost share of gross spread;
- stress net ETH.

No BTC/ETH directional return is part of the primary outcome.

## 9. Frozen minimum sample and promotion gates

All must pass:
- at least **30 completed non-overlapping hypothetical redemptions**;
- mean base net ETH per trade > 0;
- median base net ETH per trade > 0;
- >= 70% of completed trades base-net positive;
- stationary/block-bootstrap 95% lower confidence bound for mean base net ETH > 0;
- 2023 and 2024 calendar blocks each have >= 10 completed trades and non-negative mean base net ETH;
- largest single positive trade contributes <= 30% of total positive base contribution;
- stress mean net ETH > 0 using 5 bps fill haircut, 1.5x gas and 25 bps protocol-risk reserve;
- zero provenance/leakage violations.

Failure of any promotion gate means no promotion under V0.1. No sign, notional, snapshot time, venue, queue horizon, cost or period rescue after outcomes.

## 10. Source firewall

Discovery is forbidden unless `STETH_REDEMPTION_BASIS_001_SOURCE_GATE_V0_1` reaches `SOURCE_DATA_PASS` and a separate execution receipt explicitly opens Discovery.
