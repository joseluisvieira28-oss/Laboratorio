# CVFB P0E — CREDENTIAL READINESS PREFLIGHT V0.1

Date: 2026-09-19
Branch: `cross-venue-funding-basis-provenance-v0.5`
Status: **FROZEN / ZERO-S3 / ZERO-COST / SOURCE-ACCESS READINESS ONLY**

Purpose: determine whether the GitHub Actions runtime has the already-expected dedicated P0E AWS credential secrets available before any requester-pays execution is considered.

This preflight:
- MUST NOT make any AWS/S3/API request;
- MUST NOT install or invoke boto3/AWS CLI;
- MUST NOT print, hash, transform, persist or expose any credential value;
- may test only whether the expected secret strings are empty/non-empty;
- may verify the immutable P0E authorization file exists and remains source-only;
- does not authorize the P0E requester-pays probe;
- does not validate credential correctness, IAM scope or billing account;
- does not open historical object bytes, oracle values, economic outcomes, 2026, PnL or trading.

Expected secrets:
- `CVFB_P0E_AWS_ACCESS_KEY_ID`
- `CVFB_P0E_AWS_SECRET_ACCESS_KEY`
- optional `CVFB_P0E_AWS_SESSION_TOKEN`

Permitted terminal readiness states:
- `CREDENTIAL_PRESENCE_READY_FOR_MANUAL_P0E_DISPATCH`
- `CREDENTIALS_ABSENT_OR_INCOMPLETE`

Even a READY result still requires the frozen manual workflow_dispatch with the exact confirmation input and all existing P0E guards. No live trading, exchange mutation, main merge or capital is authorized.
