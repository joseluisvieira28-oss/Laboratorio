# DEFI-LIQUIDATION-SHOCK-001 — DRIFT EARLY UPPER ANCHOR V0.2 TRANSPORT FREEZE

Date: 2026-09-22
Status: TECHNICAL SUPERSESSION ONLY / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

V0.1 target/program/scientific contract remain unchanged:
- program: `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`
- target upper time: `2022-12-01T00:00:00Z`
- lower source boundary: `2022-11-04T15:17:54Z`
- official public Solana RPC only.

Technical change only:
- `getBlock.transactionDetails`: `full` -> `accounts`.
- The probe needs only transaction signatures and account keys to identify a transaction referencing the frozen Drift program.
- No instruction data, prices, returns, PnL, direction or liquidation classification is read in the anchor stage.

This mode is supported by the current Solana `getBlock` RPC schema and returns account-key metadata without full transaction instruction payloads.

All chronology, calibration, target timestamp, block-scan cap, classification and firewalls remain unchanged.

Classification remains:
- `DRIFT_EARLY_UPPER_ANCHOR_PASS`
- `DRIFT_EARLY_UPPER_ANCHOR_ACTIVITY_NOT_FOUND`
- `DRIFT_EARLY_UPPER_ANCHOR_RPC_HISTORY_BLOCKED`
- `DRIFT_EARLY_UPPER_ANCHOR_SOURCE_ANOMALY_FAIL_CLOSED`

No economic outcome is authorized.
