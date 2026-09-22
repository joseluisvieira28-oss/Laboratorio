# DEFI-LIQUIDATION-SHOCK-001 — DRIFT EARLY UPPER ANCHOR V0.3 TRANSPORT FREEZE

Date: 2026-09-22
Status: TECHNICAL SUPERSESSION ONLY / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Scientific identity is unchanged from V0.1/V0.2:
- program: `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`
- target upper time: `2022-12-01T00:00:00Z`
- lower source boundary: `2022-11-04T15:17:54Z`
- transport family: official public Solana RPC only
- liquidation classification remains forbidden during anchor discovery.

V0.2 failed operationally because `getBlocksWithLimit` with limit 40,000 repeatedly timed out on the public RPC. No scientific receipt was produced.

V0.3 changes transport granularity only:
- `getBlocksWithLimit` calibration limit: 40,000 -> 512 produced slots;
- maximum calibration rounds: 12 -> 80;
- `getBlock.transactionDetails` remains `accounts`;
- target timestamp, program, reference point, chronology, scan cap and interpretation are unchanged.

The smaller calibration batch is intended only to avoid public-RPC read timeouts. It does not change the source population or scientific boundary.

Classifications remain:
- `DRIFT_EARLY_UPPER_ANCHOR_PASS`
- `DRIFT_EARLY_UPPER_ANCHOR_ACTIVITY_NOT_FOUND`
- `DRIFT_EARLY_UPPER_ANCHOR_RPC_HISTORY_BLOCKED`
- `DRIFT_EARLY_UPPER_ANCHOR_SOURCE_ANOMALY_FAIL_CLOSED`

Firewall unchanged: prices=false; returns=false; pnl=false; direction=false; economic_outcomes=false; protected_2025_2026_market_outcomes=false; liquidation_classification=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
