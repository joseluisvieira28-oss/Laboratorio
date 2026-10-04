# MEXC APPLE REGULAR-SESSION TRANSFER — CLOSEOUT V0.2

Date: 2026-10-04
Run: 37229848123
Branch: `mexc-apple-regsession-v0.2-transfer-prereg-2026-10-04`

## Frozen verdict

`THIRD_ASSET_TRANSFER_REPLICATION_PASS__FORWARD_VALIDATION_REQUIRED`

Exact transferred cell:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon = 1 minute
- direction = FOLLOW_EXTERNAL_CONSENSUS
- no APPLE grid search

Result:
- sessions = 17
- exact common minutes = 4,573
- N = 154
- distinct signal sessions = 17
- wins = 104
- win rate = 67.5325%
- mean gross = +2.840377 bps
- median gross = +2.660010 bps
- chronological thirds = +3.665141 / +1.392842 / +3.451172 bps
- exact one-sided binomial p = 8.070222e-6
- frozen sequential alpha = 0.0125
- PASS = true

Artifact SHA256:
`36309911ed855ad4f183d5d91b12f16376709813efeaa6d30780ec30508f7996`

## Interpretation

The exact NVIDIA V0.5 rule has now survived:
1. NVIDIA discovery under 64-cell Holm correction;
2. TESLA independent cross-asset transfer;
3. APPLE independent cross-asset transfer under stricter sequential alpha spending.

This materially strengthens the hypothesis of a shared MEXC stock-futures regular-session response mechanism.

It does not prove execution feasibility.

APPLE gross edge remains below the known standard MEXC API round-trip fee floor.

No retrospective OOS, post-outcome tuning, private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.
