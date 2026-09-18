# STETH-REDEMPTION-BASIS-002 — DISCOVERY TRANSPORT REMEDIATION V0.1.1

Date: 2026-09-18
Status: **FROZEN BEFORE REMEDIATED DISCOVERY RERUN / TRANSPORT-ONLY**
Branch: `steth-redemption-basis-002-discovery-v0.1`

## Trigger

Canonical Discovery V0.1 run `35387691310` completed all preflight/source-binding checks but terminated as
`DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE`.

The failure occurred during deterministic mapping of the already-frozen 596 daily snapshots. An HTTP-successful JSON-RPC batch contained an item-level transient error:

- code: `429`
- message: provider compute-unit / throughput capacity exceeded.

No scientific Discovery verdict was produced.

## Exact permitted remediation

V0.1.1 may change only RPC transport retry handling:

- recognize transient item-level JSON-RPC rate/throughput errors inside otherwise HTTP-200 batch responses;
- retry the **exact same RPC batch** with bounded exponential backoff;
- preserve the existing frozen provider set;
- preserve all exact request methods, block tags, calldata, batch content and ordering;
- preserve fail-closed behavior for non-transient JSON-RPC errors;
- do not silently drop, replace or alter any requested item.

No hypothesis, snapshot, queue, execution, cost, statistical or promotion rule may change.

## Immutable scientific contract

Unchanged from the frozen V0.1 protocol and implementation:

- Lab: `STETH-REDEMPTION-BASIS-002`
- MVE: `STETH002-REDEEM-CONVERGENCE-H14-V01`
- 596 daily 12:00 UTC snapshots, 2023-05-16 through 2024-12-31
- 10 ETH fixed notional
- Curve legacy ETH/stETH route
- Lido WithdrawalQueue exact finalization/checkpoint reconstruction
- one active position at a time
- 14-day maximum wait
- base/stress quote haircuts, gas, opportunity-cost and protocol-risk reserves unchanged
- bootstrap reps/seed/block logic unchanged
- all Discovery gates unchanged
- source binding run `35386033845` unchanged
- 2025/2026 locked
- no live trading / orders / wallets / exchange mutation / main merge.

## Rerun interpretation

The V0.1.1 rerun is a continuation of the same frozen Discovery, not a new scientific experiment.

Permitted terminal classes remain exactly:

- `DISCOVERY_INSUFFICIENT_SAMPLE`
- `DISCOVERY_NO_REDEMPTION_EDGE`
- `DISCOVERY_REDEMPTION_EDGE_PASS_REQUIRES_SEPARATE_REPLICATION`
- `DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE`

No outcome from the failed V0.1 transport run may be used for tuning or selection.
