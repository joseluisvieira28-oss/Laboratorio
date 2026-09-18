# STETH-REDEMPTION-BASIS-002 — DISCOVERY RPC THROUGHPUT REMEDIATION V0.1A

Date: 2026-09-18
Status: FROZEN AFTER TECHNICAL FAILURE / BEFORE RETRY
Branch: steth-redemption-basis-002-discovery-v0.1

## Triggering failure

Canonical Discovery run:
- run: 35387691310
- artifact: 10566369698
- artifact digest: sha256:350484c0d75290fc37134abdbd304300390d67ce3886113f573b5c7714cdb1e7
- classification: DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE

Exact failure:
HTTP/RPC throughput throttling during batched historical block-header acquisition:
`batch RPC item 6 failed: {'code': 429, 'message': 'Your app has exceeded its compute units per second capacity...'}`

The failure occurred during frozen 596-snapshot timestamp mapping after 15 vectorized binary-search rounds.

## Scientific interpretation

This is a transport failure only.

It is NOT:
- DISCOVERY_NO_REDEMPTION_EDGE;
- DISCOVERY_INSUFFICIENT_SAMPLE;
- a failed cost gate;
- a failed PnL gate;
- a failed claim reconstruction;
- a failed queue-horizon gate.

No scientific parameter may change.

## Authorized remediation

Transport-only changes:
1. treat per-item JSON-RPC code 429 and provider-equivalent transient overload codes as retryable;
2. retry the same exact batch with exponential backoff;
3. if repeated transient item-level throttling persists, recursively split the exact batch into smaller sub-batches while preserving request order and exact request contents;
4. never substitute a different block, timestamp, method, calldata, contract, notional or provider quorum rule;
5. require the same exact 2-of-3 equality after transport recovery.

No cached economic values from the failed run may be used.

## Frozen science unchanged

Unchanged:
- 596 daily snapshots;
- 2023-05-16 through 2024-12-31;
- 12:00 UTC;
- 10 ETH;
- Curve legacy ETH/stETH only;
- Lido WithdrawalQueue only;
- 2 bps base / 5 bps stress fill;
- 800k gas;
- 1.25x baseFee;
- 1.5x stress gas;
- 10 bps / 25 bps risk reserve;
- 14-day maximum wait;
- exact checkpoint/share-rate claim reconstruction;
- overlap rules;
- sample gates;
- bootstrap;
- promotion gates;
- 2025/2026 firewall.

## Retry authority

One canonical V0.1A retry is authorized after:
- compile PASS;
- synthetic self-test PASS;
- exact source binding PASS;
- exact protocol/freeze identity PASS;
- explicit proof that item-level 429 is retried/split without changing request payload semantics.

No outcome-based code change is authorized.
