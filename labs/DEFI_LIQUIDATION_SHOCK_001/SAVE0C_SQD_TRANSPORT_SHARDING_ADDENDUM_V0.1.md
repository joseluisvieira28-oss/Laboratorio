# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C SQD TRANSPORT SHARDING ADDENDUM V0.1

Date: 2026-09-26
Status: FROZEN TECHNICAL REMEDIATION / SOURCE-ONLY / OUTCOME-BLIND

## Trigger

The authoritative Marginfi+Save0c census run `36114038836` is scientifically healthy but has four unresolved Save0c monthly windows caused by runner/runtime interruption:

- 2022-02-01 -> 2022-03-01: original job interrupted by runner shutdown; dedicated monthly retry `36185816634` was also interrupted by runner shutdown after ~52 minutes.
- 2024-10-01 -> 2024-11-01: cancelled at ~180.6 minutes.
- 2024-11-01 -> 2024-12-01: cancelled at ~180.3 minutes.
- 2024-12-01 -> 2025-01-01: cancelled at ~180.5 minutes.

No source anomaly or scientific mismatch was observed in these failures. The remaining Marginfi population is 23/23 monthly partitions successful; all other completed Save0c partitions are successful.

## Frozen remediation

Do not alter protocol identity, Save/Solend program, native tag 0x0c, source window, exact UTC membership, +16 slot envelope, success/failure semantics, or RAW authority.

Re-execute exactly the four unresolved windows as contiguous, non-overlapping <=7-day shards using the frozen original census runner from SHA:
`40d42e4ffdc85502d5965115a434c29fc08a6704`

Replacement evidence is admissible only if every shard completes, exact coverage is gap-free/overlap-free, stream_complete=true and anomaly_count=0.

Cancelled/interrupted monthly artifacts are non-authoritative and must not substitute for replacement shards.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
