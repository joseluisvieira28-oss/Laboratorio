# STETH-REDEMPTION-BASIS-002 — DISCOVERY IMPLEMENTATION FREEZE V0.1

Date: 2026-09-18
Status: FROZEN BEFORE FIRST ECONOMIC OUTCOME ACQUISITION
Branch: steth-redemption-basis-002-discovery-v0.1

## Immutable upstream authority

Source Gate:
- run: 35386033845
- artifact: 10563803871
- artifact digest: sha256:d1c371d5dda3718bb044f9a6b2cd628d8c35cd55af8ba85040375ee903110f53
- classification: SOURCE_DATA_PASS
- first mapped snapshot block: 17,272,128
- final mapped snapshot block: 21,522,315

Final Pre-Discovery Protocol:
- commit: 80c9a30d4abcedbc86a951228fb0105c1cd094e9
- file: research/steth_redemption_basis_002/STETH_REDEMPTION_BASIS_002_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1.md

Nothing below changes the economic hypothesis, notional, clock, costs, queue horizon, sample gates, promotion gates, universe or protected-period firewall. This file freezes implementation details that must be decided before any Discovery outcome is opened.

## 1. Snapshot mapping

Frozen observation targets remain exactly 596 daily timestamps:
2023-05-16T12:00:00Z through 2024-12-31T12:00:00Z inclusive.

Each target maps to the first Ethereum block with block.timestamp >= target.

Implementation:
- use the already-proven archive provider set;
- binary-search headers with one provider;
- verify the resulting exact block number, hash and timestamp against at least one additional provider;
- a mapping without two-provider exact agreement is a technical/provenance failure;
- no snapshot may be dropped.

No header after 2024-12-31T23:59:59Z may be used.

## 2. Point-in-time state quorum

At every mapped snapshot, require exact equality from at least 2 of the frozen 3 archive providers for:
- Curve get_dy(0,1,10 ETH);
- WithdrawalQueue getLastRequestId();
- WithdrawalQueue unfinalizedStETH();
- stETH getSharesByPooledEth(acquired stETH after base 2 bps fill haircut);
- snapshot block baseFeePerGas via the canonical block header.

If exact two-provider equality cannot be obtained for a required field, the snapshot is not silently dropped; Discovery terminates TECHNICAL_OR_PROVENANCE_FAILURE.

## 3. Full acquired stETH submitted in next block

The Final Pre-Discovery Protocol freezes submission in the next block.

To preserve rebasing-token semantics exactly:
1. at snapshot t, compute the stETH shares represented by acquired_steth_base_t with getSharesByPooledEth();
2. at block t+1, compute the full stETH balance represented by those same shares with getPooledEthByShares();
3. submit that full next-block balance hypothetically;
4. compute the request shares at t+1 with getSharesByPooledEth(request_steth_t_plus_1).

This captures any rebase/rounding between the acquisition block and the next block without looking beyond t+1.

The frozen queue position remains exactly:
getLastRequestId(t) + 1

as specified by the Final Pre-Discovery Protocol.

## 4. Canonical event acquisition

Use canonical Ethereum structural logs with full SQD continuation semantics:
- if a response contains rows, continue from the last returned block + 1;
- if a healthy response contains zero rows, the requested window is covered and continuation is request_to + 1;
- returned block numbers must be monotonic and within the exact request window;
- canonical identity is transactionHash + logIndex and duplicates are terminal provenance failures.

Required full-period events:

### WithdrawalQueue
WithdrawalsFinalized(uint256,uint256,uint256,uint256,uint256)

Acquire from the canonical V2 activation block 17,266,004 through the frozen final snapshot block 21,522,315.

Decode:
- indexed from request id;
- indexed to request id;
- amountOfETHLocked;
- sharesToBurn;
- event timestamp.

### stETH
TokenRebased(uint256,uint256,uint256,uint256,uint256,uint256,uint256)

Acquire from at least 7 calendar days before the first snapshot through the frozen final snapshot block.

Decode:
- indexed reportTimestamp;
- timeElapsed;
- preTotalShares;
- preTotalEther;
- postTotalShares;
- postTotalEther;
- sharesMintedAsFees.

No 2025/2026 event is permitted.

## 5. Frozen trailing 7-day reward-rate implementation

For snapshot timestamp t:

Select canonical TokenRebased events with:
t - 7 days < reportTimestamp <= t

For each event:
pre_share_rate = preTotalEther / preTotalShares
post_share_rate = postTotalEther / postTotalShares

event growth factor:
g_i = post_share_rate / pre_share_rate

Seven-day compounded growth factor:
G_7d = product(g_i)

Trailing annualized reward rate:
APR_7d = G_7d^(365/7) - 1

At least one canonical TokenRebased event must exist in the trailing window. Otherwise no signal is permitted for that snapshot.

No clipping of negative rates.
No later smoothing.
No alternate lookback.

## 6. Frozen queue-throughput implementation

At snapshot t:

trailing_finalized_eth_14d =
sum(amountOfETHLocked) for canonical WithdrawalsFinalized events with:
t - 14 days < event_timestamp <= t

If trailing_finalized_eth_14d == 0:
no signal.

daily_throughput =
trailing_finalized_eth_14d / 14

estimated_queue_days =
unfinalizedStETH(t) / daily_throughput

Apply the already-frozen floor:
estimated_queue_days = max(0.25, estimated_queue_days)

If estimated_queue_days > 14:
no signal.

No alternate throughput denominator or lookback.

## 7. Frozen integer/cost arithmetic

Base fill:
acquired_steth_base_wei = floor(curve_get_dy_wei * 9998 / 10000)

Stress fill:
acquired_steth_stress_wei = floor(curve_get_dy_wei * 9995 / 10000)

Base gas:
gas_base_wei = ceil(800000 * baseFeePerGas * 1.25)
= 800000 * baseFeePerGas * 5 / 4, rounded upward

Stress gas:
gas_stress_wei = ceil(gas_base_wei * 1.5)

Base risk reserve:
0.010000 ETH

Stress risk reserve:
0.025000 ETH

Estimated and realized foregone-reward costs are rounded upward to the nearest wei.

## 8. Frozen signal computation

Use only point-in-time information available by snapshot t.

Estimated reward cost:
ceil(acquired_steth_base * APR_7d * estimated_queue_days / 365)

Estimated nominal redemption at entry:
acquired_steth_base

unless point-in-time protocol state already proves a lower amount. No future checkpoint is used in the signal.

Base estimated edge:
estimated_nominal_redemption
- 10 ETH
- estimated_reward_cost
- base_gas
- base_risk_reserve

Signal iff:
- all source fields exist and pass provenance;
- estimated_queue_days <= 14;
- estimated_edge > 0.

No secondary threshold.

## 9. Hypothetical finalization mapping

For a signaled hypothetical position:
queue_position = getLastRequestId(t) + 1

Find the first canonical WithdrawalsFinalized event AFTER t satisfying:
event.from <= queue_position <= event.to

That event is the hypothetical finalization event under the prospectively frozen small-perturbation/FIFO assumption already encoded by the queue-position rule.

If no such event exists inside the protected 2023-2024 source envelope:
classify that position RIGHT_CENSORED_PROTECTED_BOUNDARY.
Do not open 2025.

Holding time:
(event.timestamp - snapshot_timestamp) / 86400

If holding time > 14 calendar days:
classify the position OPERATIONAL_WAIT_FAILURE.
Do not extend the horizon.

## 10. Exact checkpoint / claim reconstruction

WithdrawalQueue V2 creates exactly one checkpoint for each _finalize() call immediately before emitting WithdrawalsFinalized.

The checkpoint mapping uses:
keccak256("lido.WithdrawalQueue.checkpoints")

For a hypothetical queue_position finalized by a canonical WithdrawalsFinalized event:

1. determine the canonical checkpoint index by the ordinal of that WithdrawalsFinalized event since V2 activation, using block/log ordering;
2. at the finalization block, read the proxy storage mapping entry:
   Checkpoint(fromRequestId, maxShareRate);
3. require checkpoint.fromRequestId == event.from;
4. otherwise terminate with provenance failure.

Hypothetical request share rate:
request_share_rate =
floor(request_steth_wei * 1e27 / request_shares)

Exact claim:
- if request_share_rate > checkpoint.maxShareRate:
  claim_wei = floor(request_shares * checkpoint.maxShareRate / 1e27)
- else:
  claim_wei = request_steth_wei

This reproduces WithdrawalQueueBase._calculateClaimableEther for the hypothetical single request without inventing a 1:1 override.

## 11. Realized opportunity cost

The entry-time trailing APR_7d remains the opportunity-cost rate.

The future-known quantity used only in realized outcome is the actual holding time.

realized_reward_cost =
ceil(request_steth_wei * APR_7d_at_entry * actual_holding_days / 365)

No future reward-rate selection is used to improve the trade.

## 12. Base and stress realized outcome

Base net ETH:
claim_wei
- 10 ETH
- realized_reward_cost_base
- base_gas
- base_risk_reserve

Stress net ETH uses:
- the stress 5 bps acquired amount;
- corresponding next-block stress request amount/shares;
- the same canonical finalization checkpoint;
- realized reward cost on the stress request amount;
- 1.5x base gas;
- 25 bps risk reserve.

No early Curve exit.
No stop.
No take-profit.

## 13. Overlap

One position maximum.

After a completed finalization:
the first later daily snapshot may be considered.

While a position remains unfinalized:
all later daily candidate signals are ignored.

If the active position becomes OPERATIONAL_WAIT_FAILURE:
the MVE has suffered an operational failure and promotion is impossible under V0.1.
The simulation does not pretend the capital was released at day 14.

RIGHT_CENSORED_PROTECTED_BOUNDARY is reported separately and is not assigned an invented PnL.

## 14. Bootstrap

For completed non-overlapping trades only:

- deterministic RNG seed: 20260918;
- circular moving-block bootstrap;
- 10,000 replications;
- block length = max(2, ceil(n^(1/3)));
- each replication samples circular blocks until n observations are obtained;
- statistic = mean base net ETH per completed trade;
- 95% lower confidence bound = empirical 2.5th percentile.

No alternative block length or bootstrap rescue after outcomes.

## 15. Frozen adjudication

Sample gate:
completed non-overlapping hypothetical redemptions >= 30.

Promotion gates are exactly those in the Final Pre-Discovery Protocol plus:

- zero OPERATIONAL_WAIT_FAILURE positions.

Classification:

DISCOVERY_INSUFFICIENT_SAMPLE
if completed sample < 30 and there is no technical/provenance failure.

DISCOVERY_NO_REDEMPTION_EDGE
if sample gate passes but any frozen promotion gate fails, including operational-wait failure.

DISCOVERY_REDEMPTION_EDGE_PASS_REQUIRES_SEPARATE_REPLICATION
only if every frozen gate passes.

DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE
if required exact source/provenance reconstruction fails.

A RIGHT_CENSORED_PROTECTED_BOUNDARY position does not authorize 2025 access and is reported as censored.

## 16. Hard firewall

No 2025.
No 2026.
No live trading.
No wallet.
No order.
No exchange mutation.
No leverage deployment.
No main merge.
No post-outcome tuning.
No venue/notional/timing/cost/horizon rescue.
