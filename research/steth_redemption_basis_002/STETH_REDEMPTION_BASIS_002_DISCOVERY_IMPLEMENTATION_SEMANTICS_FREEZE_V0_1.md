# STETH-REDEMPTION-BASIS-002 — DISCOVERY IMPLEMENTATION SEMANTICS FREEZE V0.1

Status: **FROZEN BEFORE DISCOVERY OUTCOMES**
Date: **2026-09-18**
Parent protocol commit: `80c9a30d4abcedbc86a951228fb0105c1cd094e9`

This document resolves implementation ambiguities only. It may not change the economic hypothesis, venue, direction, notional, costs, snapshot clock, horizon or promotion thresholds frozen in the FINAL PRE-DISCOVERY PROTOCOL V0.1.

## 1. Canonical snapshot mapping

For all 596 UTC dates from 2023-05-16 through 2024-12-31:

- target timestamp is exactly 12:00:00 UTC;
- snapshot block is the first canonical Ethereum block with timestamp >= target;
- its predecessor must have timestamp < target;
- mapping is obtained by deterministic batched binary search;
- block number, hash and timestamp require exact 2-of-3 quorum across the same three archive providers frozen by the source gate;
- any unresolved quorum is terminal technical/provenance failure;
- no block with timestamp in 2025 or 2026 may be read.

The exact source-gate edge mappings remain hard guards:
- first snapshot block = 17,272,128;
- final snapshot block = 21,522,315.

## 2. Point-in-time state quorum

At each snapshot block, exact 2-of-3 archive-provider quorum is required for:

- Curve `get_dy(0,1,10 ether)`;
- WithdrawalQueue `getLastRequestId()`;
- WithdrawalQueue `unfinalizedStETH()`;
- canonical block baseFeePerGas.

No CEX price, external price index or later mark is allowed.

## 3. Trailing 7-day stETH net reward APR

Only canonical `TokenRebased` events whose block timestamp is <= snapshot timestamp and > snapshot timestamp - 7*86400 are eligible.

For each event:

`preShareRate = preTotalEther / preTotalShares`

`postShareRate = postTotalEther / postTotalShares`

The event growth multiplier is:

`g_i = postShareRate / preShareRate`

The trailing 7-day stETH net growth multiplier is the product of all eligible `g_i`.

The frozen annualized simple APR is:

`APR_7D = (product(g_i) - 1) * 365 / 7`

At least one eligible TokenRebased event is required. No clipping of negative APR is allowed.

This uses the same net share-rate economics documented by Lido for TokenRebased.

## 4. Trailing 14-day withdrawal throughput

Only canonical `WithdrawalsFinalized` events with event timestamp <= snapshot timestamp and > snapshot timestamp - 14*86400 are eligible.

`throughput_14d_eth = sum(amountOfETHLocked)`

`daily_throughput_eth = throughput_14d_eth / 14`

If throughput is zero, the snapshot is not signal-eligible.

Estimated queue days:

`estimated_queue_days = max(0.25, unfinalizedStETH / daily_throughput_eth)`

If estimated queue days > 14, there is no signal.

## 5. Signal arithmetic

All contract quantities are first retained as exact integer wei.

Base acquired stETH:

`acquired_base = floor(curve_get_dy * 0.9998)`

Stress acquired stETH:

`acquired_stress = floor(curve_get_dy * 0.9995)`

Base gas:

`gas_base_eth = 800000 * (1.25 * baseFeePerGas)`

implemented exactly as integer wei:

`gas_base_wei = 800000 * baseFeePerGas * 5 // 4`

Base reserve:

`0.010000 ETH`

Stress reserve:

`0.025000 ETH`

Estimated reward opportunity cost:

`acquired_base * APR_7D * estimated_queue_days / 365`

The base signal is true iff the FINAL PRE-DISCOVERY predictor is strictly > 0.

No additional threshold or tolerance is permitted.

## 6. Hypothetical request shares

The FINAL PRE-DISCOVERY protocol assumes the withdrawal request is submitted in the next block.

Therefore, for a signaled snapshot at block `t`:

- submission block = `t + 1`;
- submission block timestamp must still be <= 2024-12-31T23:59:59Z;
- exact 2-of-3 quorum is required for stETH `getSharesByPooledEth(acquired_amount)` at the submission block;
- base and stress acquired amounts are converted separately;
- the integer output is the hypothetical request share amount exactly as Lido's WithdrawalQueue request path would obtain it.

Hypothetical queue request id remains:

`getLastRequestId(t) + 1`

No later queue id is substituted.

## 7. Canonical finalization and maxShareRate

The finalization event is the first canonical `WithdrawalsFinalized` after the submission whose emitted `to` request id is >= the hypothetical queue request id.

The event's timestamp is the finalization timestamp.

The checkpoint `maxShareRate` applied to that finalization must be reconstructed from the same canonical transaction:

Accepted transaction calldata forms only:

1. direct WithdrawalQueue
   `finalize(uint256,uint256)`
   where arg0 equals the event `to` and arg1 is `maxShareRate`;

2. Lido
   `collectRewardsAndProcessWithdrawals(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)`
   where arg5 equals the event `to` and arg6 is the withdrawal `maxShareRate`.

If neither exact binding is available, or values disagree under provider quorum, Discovery fails closed.

No inferred, averaged or fitted maxShareRate is allowed.

## 8. Protocol-exact hypothetical claim amount

For each base/stress hypothetical request:

`requestShareRate = acquiredStETH * 1e27 // requestShares`

If:

`requestShareRate > checkpointMaxShareRate`

then:

`claimWei = requestShares * checkpointMaxShareRate // 1e27`

else:

`claimWei = acquiredStETH`

This reproduces WithdrawalQueueBase `_calculateClaimableEther` / `_calcBatch` economics and integer rounding for a one-request hypothetical batch element.

## 9. Realized wait and opportunity cost

Realized wait begins at the submission block timestamp and ends at canonical finalization timestamp.

`holding_days = (finalization_ts - submission_ts) / 86400`

The realized opportunity cost uses only the point-in-time APR frozen at entry:

`realized_reward_cost = acquiredStETH * APR_7D_entry * holding_days / 365`

Future TokenRebased outcomes are not used to re-estimate the entry APR.

## 10. Fourteen-day operational horizon

If no eligible canonical finalization occurs within 14*86400 seconds after submission:

- classification for that position is `OPERATIONAL_HORIZON_FAILURE`;
- it is not silently extended;
- it is not dropped from diagnostics;
- the position blocks later candidate signals until the 14-day horizon expires;
- any such failure causes the Discovery promotion gate to fail.

No synthetic loss is assigned beyond the frozen costs because the protocol did not freeze a forced-sale exit.

## 11. 2025/2026 firewall and right-censoring

No 2025/2026 chain data may be accessed.

If a signaled position cannot be adjudicated through its full 14-day horizon using data ending 2024-12-31T23:59:59Z:

- mark it `PROTECTED_PERIOD_CENSORED`;
- do not assume success or failure;
- do not count it as completed;
- Discovery cannot return an edge PASS while such a position could change the verdict;
- final classification becomes `DISCOVERY_PROTECTED_PERIOD_BLOCKED` unless the position was already canonically finalized inside 2024.

## 12. Non-overlap

At most one position is active.

- completed position: next daily snapshot after finalization may be considered;
- operational-horizon failure: next daily snapshot after the 14-day failure time may be considered;
- protected-period-censored position: no later snapshot may create another position.

Skipped overlapping snapshots remain in the 596-snapshot census as `OVERLAP_SKIPPED`.

## 13. Realized net outcomes

Base:

`net_base = claim_base - 10 ETH - realized_reward_cost_base - gas_base - 0.010 ETH`

Stress:

- 5 bps acquired-stETH haircut;
- protocol-exact stress claim from stress shares;
- realized opportunity cost on stress acquired amount using the same entry APR and actual holding time;
- gas = `1.5 * gas_base`;
- reserve = 0.025 ETH.

No other fee, threshold or rescue term may be introduced after outcomes.

## 14. Bootstrap freeze

If there are at least 30 completed non-overlapping trades, the frozen confidence procedure is:

- statistic: arithmetic mean of base net ETH;
- stationary bootstrap;
- expected block length: `max(2, round(sqrt(N)))` completed trades;
- continuation probability: `1 - 1/block_length`;
- 10,000 replicates;
- PRNG seed: `20260918`;
- one-sided 95% lower confidence bound = empirical 5th percentile of bootstrap means.

No alternate bootstrap, seed or block length may rescue the result.

## 15. Exact final classifications

Priority order:

1. transport/provenance/receipt violation -> `DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE`;
2. unresolved protected-period signal -> `DISCOVERY_PROTECTED_PERIOD_BLOCKED`;
3. fewer than 30 completed non-overlapping redemptions -> `DISCOVERY_INSUFFICIENT_SAMPLE`;
4. any operational-horizon failure or any frozen promotion gate fails -> `DISCOVERY_NO_REDEMPTION_EDGE`;
5. all frozen gates pass -> `DISCOVERY_REDEMPTION_EDGE_PASS_REQUIRES_SEPARATE_REPLICATION`.

No Discovery PASS authorizes production, wallets, live trading, exchange mutation or main merge.
